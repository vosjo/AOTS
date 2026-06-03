from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from AOTS.custom_permissions import IsAllowedOnProject, _get_object_project


def get_object_if_allowed(model, request, pk, select_related=None, require_edit=False):
    """
    Load an object by primary key and enforce project permissions.
    """
    queryset = model.objects.all()
    if select_related:
        queryset = queryset.select_related(*select_related)
    obj = get_object_or_404(queryset, pk=pk)

    if require_edit:
        if request.user.is_anonymous or not request.user.can_edit(obj):
            raise PermissionDenied()
        return obj

    permission = IsAllowedOnProject()
    if not permission.has_object_permission(request, None, obj):
        raise PermissionDenied()

    return obj


def check_project_access(user, project, require_add=False):
    """
    Verify that a user may read or add objects in a project.
    """
    if require_add:
        if not user.can_add(project):
            raise PermissionDenied()
    elif user.is_anonymous:
        if not project.is_public:
            raise PermissionDenied()
    elif not user.can_read(project):
        raise PermissionDenied()
