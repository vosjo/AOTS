"""Helpers for project-scoped django-filter FilterSets."""

from django_filters import rest_framework as filters


def project_id_from_mapping(data) -> int | None:
    if not data:
        return None
    project = data.get('project')
    if project in (None, ''):
        return None
    try:
        return int(project)
    except (TypeError, ValueError):
        return None


def project_pk_filter(*, field_name='project'):
    """Filter by project primary key without exposing all Project rows."""
    return filters.NumberFilter(field_name=field_name, lookup_expr='exact')
