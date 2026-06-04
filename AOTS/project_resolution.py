"""
Resolve the Project instance an arbitrary model instance belongs to.
"""

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
