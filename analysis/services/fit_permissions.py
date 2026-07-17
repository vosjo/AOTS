"""Fit-level permissions for multi-contributor analyses."""

from __future__ import annotations

from analysis.categories import AnalysisCategory
from analysis.models.analysis_fit import AnalysisFit

MULTI_FIT_CATEGORIES = frozenset({
    AnalysisCategory.RV_CURVE,
    AnalysisCategory.SPECTRAL_FIT,
    AnalysisCategory.LIGHTCURVE_FIT,
    AnalysisCategory.SED_FIT,
})


def category_supports_multi_fit(category: str | None) -> bool:
    return category in MULTI_FIT_CATEGORIES


def user_can_contribute_fit(user, analysis) -> bool:
    return user.can_add(analysis.project)


def user_can_set_best_fit(user, analysis) -> bool:
    if user.is_superuser:
        return True
    return user._project_in_user_set(analysis.project, 'readwrite_projects')


def user_can_edit_fit(user, fit: AnalysisFit) -> bool:
    if user.is_superuser:
        return True
    project = fit.analysis.project
    if user._project_in_user_set(project, 'readwrite_projects'):
        return True
    if (
        fit.uploaded_by_id == user.pk
        and user._project_in_user_set(project, 'readwriteown_projects')
    ):
        return True
    return False


def user_can_delete_fit(user, fit: AnalysisFit) -> bool:
    if user.is_superuser:
        return True
    project = fit.analysis.project
    if user._project_in_user_set(project, 'readwrite_projects'):
        return True
    if (
        fit.uploaded_by_id == user.pk
        and user._project_in_user_set(project, 'readwriteown_projects')
    ):
        return True
    return False
