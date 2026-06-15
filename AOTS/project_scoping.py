"""Helpers to keep related rows within one project."""

from django.core.exceptions import ValidationError


def require_same_project(project, related, label: str) -> None:
    """Raise ValidationError when related.project_id differs from project."""
    if project is None or related is None:
        return
    related_project_id = getattr(related, 'project_id', None)
    if related_project_id is None:
        return
    if related_project_id != project.pk:
        raise ValidationError(f'{label} must belong to the same project.')


def require_queryset_same_project(project, queryset, label: str) -> None:
    """Raise ValidationError when any row in queryset belongs to another project."""
    if project is None:
        return
    for related in queryset:
        require_same_project(project, related, label)


def assert_plot_belongs_to_project(obj, project) -> None:
    """Guard plotting helpers when an explicit project is supplied."""
    if project is None or obj is None:
        return
    require_same_project(project, obj, type(obj).__name__)
