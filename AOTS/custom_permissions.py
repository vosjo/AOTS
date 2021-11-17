
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import permissions

from stars.models import Project


class IsAllowedOnProject(permissions.BasePermission):
   """
   Custom permission to allow users to see/edit/add/remove objects only if
   they have permission to perform those actions for the project this object belongs to.
   """

   def has_object_permission(self, request, view, obj):

      # show the object if the user is allowed to see this project (GET, HEAD or OPTIONS)
      if request.method in permissions.SAFE_METHODS:
         if request.user.is_anonymous:
            return obj.project.is_public
         else:
            return request.user.can_read(obj.project)

      # User can add objects in this project?
      if request.method == ['POST'] and not request.user.is_anonymous:
         return request.user.can_add(obj.project)

      # check if the user is allowed to edit/delete this specific object
      if request.method in ['PUT', 'PATCH', 'DELETE'] and not request.user.is_anonymous:
         return request.user.can_edit(obj)


      return False


def get_allowed_objects_to_view_for_user(qs, user):
    """
    Function that will limit the provided queryset to the objects that
    the provided user can see.

    This filtering is based on the project that the object belongs too.
    An anonymous user can see objects from all public projects. A logged
    in user can also see private projects that he/she has viewing rights
    for.

    (for some reason qs1.union(qs2) can not be used here instead of
    using th | operator!!!)
    """

    #   Check if project is public
    public = qs.filter(project__is_public__exact=True)

    #   Check if user is logged in ...
    if user.is_anonymous:
        #   ... return the "public" queryset if not
        return public
    else:
        #   Check if user is allowed to view the project ...
        restricted = qs.filter(
            project__pk__in=user.get_read_projects().values('pk')
            )
        if len(restricted) > 0:
            #   ... if this is the case return the specific queryset ...
            return restricted
        else:
            #   ... if not, return the public queryset
            return public


def check_user_can_view_project(function):
   """
   Decorator that loads the function if the user is allowed to see the project,
   redirects to login page otherwise.
   """
   def wrapper(request, *args, **kwargs):
      user = request.user
      try:
         project = Project.objects.get(slug=kwargs['project'])
      except Exception:
         messages.error(request, "That page requires login to view")
         return redirect('login')

      if request.user.is_anonymous and project.is_public:
         return function(request, *args, **kwargs)
      elif not request.user.is_anonymous and request.user.can_read(project):
         return function(request, *args, **kwargs)
      else:
         messages.error(request, "Project: {} requires login to see".format(project))
         return redirect('login')

   return wrapper
