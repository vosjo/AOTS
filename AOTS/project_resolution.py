"""
Resolve the Project instance an arbitrary model instance belongs to.
"""

from django.core.exceptions import ObjectDoesNotExist

from stars.models import Project


def get_object_project(obj):
    """
    Return the Project for permission checks and queryset filtering.
    """
    if isinstance(obj, Project):
        return obj

    if hasattr(obj, 'project_id') and obj.project_id is not None:
        return obj.project

    if hasattr(obj, 'star_id') and obj.star_id is not None:
        return obj.star.project

    raise AttributeError(f'Cannot determine project for {obj!r}')


def resolve_project_from_request(request, *, body_field='project', header_name='HTTP_PROJECTID'):
    """
    Resolve a Project from JSON/form body or a request header.

    Returns (project, error_response). error_response is a DRF Response or None.
    """
    from rest_framework import status
    from rest_framework.response import Response

    project_pk = None
    if hasattr(request, 'data') and request.data.get(body_field) is not None:
        project_pk = request.data.get(body_field)
    elif hasattr(request, 'POST') and request.POST.get(body_field):
        project_pk = request.POST.get(body_field)
    elif request.META.get(header_name):
        project_pk = request.META.get(header_name)

    if project_pk is None:
        return None, Response(
            {
                'detail': (
                    f'Missing project (body field "{body_field}" or '
                    f'{header_name.replace("HTTP_", "")} header).'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Project.objects.get(pk=int(project_pk)), None
    except ValueError:
        try:
            return Project.objects.get(name__exact=project_pk), None
        except ObjectDoesNotExist:
            return None, Response(
                {'detail': 'Unknown project.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ObjectDoesNotExist:
        return None, Response(
            {'detail': 'Unknown project.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
