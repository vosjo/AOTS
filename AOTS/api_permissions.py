
import copy

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
   """
   Custom permission to only allow owners of an object to edit it.
   """

   def has_object_permission(self, request, view, obj):
      # Read permissions are allowed to any request,
      # so we'll always allow GET, HEAD or OPTIONS requests.
      if request.method in permissions.SAFE_METHODS:
            return True

      # Write permissions are only allowed to the owner of the snippet.
      return obj.added_by == request.user 


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
   Function that will limit the provided queryset to the objects that the provided user can see.
   
   This filtering is based on the project that the object belongs too. An anonymous user can 
   see objects from all public projects. A logged in user can also see private projects that 
   he/she has viewing rights for.
   """
   
   if user.is_anonymous:
      qs = qs.filter(project__is_public__exact=True)
   else:
      public = qs.filter(project__is_public__exact=True)
      qs = public.union( qs.filter(project__pk__in=user.get_read_projects().values('pk')) )
         
   return qs
