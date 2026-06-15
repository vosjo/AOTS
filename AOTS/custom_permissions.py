from django.contrib import messages
from django.shortcuts import redirect
from rest_framework import permissions
from AOTS.project_resolution import get_object_project
from stars.models import Project


class IsAllowedOnProject(permissions.BasePermission):
    """
    Custom permission to allow users to see/edit/add/remove objects only if
    they have permission to perform those actions for the project this object belongs to.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_anonymous:
            return False
        if request.method == 'POST':
            project = _get_project_from_request(request)
            if project is None:
                return False
            return request.user.can_add(project)
        return True

    def has_object_permission(self, request, view, obj):
        project = get_object_project(obj)

        if request.method in permissions.SAFE_METHODS:
            if request.user.is_anonymous:
                return project.is_public
            return request.user.can_read(project)

        if request.user.is_anonymous:
            return False

        if request.method == 'DELETE':
            return request.user.can_delete(obj)

        if request.method in ('PUT', 'PATCH'):
            return request.user.can_edit(obj)

        return False


def _get_project_from_request(request):
    data = getattr(request, 'data', None) or {}

    project_id = data.get('project')
    if project_id is not None:
        try:
            return Project.objects.get(pk=project_id)
        except (Project.DoesNotExist, ValueError, TypeError):
            return None

    star_id = data.get('star')
    if star_id is not None:
        from stars.models import Star
        try:
            return Star.objects.select_related('project').get(pk=star_id).project
        except (Star.DoesNotExist, ValueError, TypeError):
            return None

    analysis_id = data.get('analysis')
    if analysis_id is not None:
        from analysis.models import Analysis
        try:
            return Analysis.objects.select_related('project').get(pk=analysis_id).project
        except (Analysis.DoesNotExist, ValueError, TypeError):
            return None

    spectrum_id = data.get('spectrum')
    if spectrum_id is not None:
        from observations.models import Spectrum
        try:
            return Spectrum.objects.select_related('project').get(pk=spectrum_id).project
        except (Spectrum.DoesNotExist, ValueError, TypeError):
            return None

    return None


def get_allowed_objects_to_view_for_user(qs, user, parameter_switch=False):
    """
    Function that will limit the provided queryset to the objects that
    the provided user can see.

    This filtering is based on the project that the object belongs too.
    An anonymous user can see objects from all public projects. A logged
    in user can also see private projects that he/she has viewing rights
    for.
    """
    if parameter_switch:
        public = qs.filter(star__project__is_public__exact=True)
    else:
        public = qs.filter(project__is_public__exact=True)

    if user.is_anonymous:
        return public

    if parameter_switch:
        restricted = qs.filter(
            star__project__pk__in=user.get_read_projects().values('pk')
        )
    else:
        restricted = qs.filter(
            project__pk__in=user.get_read_projects().values('pk')
        )

    return (public | restricted).distinct()


def check_user_can_view_project(function):
    """
    Decorator that loads the function if the user is allowed to see the project,
    redirects to login page otherwise.
    """

    def wrapper(request, *args, **kwargs):
        try:
            project = Project.objects.get(slug=kwargs['project'])
        except Project.DoesNotExist:
            messages.error(request, 'That page requires login to view')
            return redirect('login')

        if request.user.is_anonymous:
            if not project.is_public:
                messages.error(request, 'Project: {} requires login to see'.format(project))
                return redirect('login')
        elif not request.user.can_read(project):
            messages.error(request, 'Project: {} requires login to see'.format(project))
            return redirect('login')

        return function(request, *args, **kwargs)

    return wrapper
