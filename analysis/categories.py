"""
Fixed analysis category registry (replaces per-project Method entities).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import models

from analysis.models.default_values import GENERIC, SED


class AnalysisCategory(models.TextChoices):
    RV_SOLUTION = 'rv_solution', 'RV solution'
    RV_CURVE = 'rv_curve', 'RV curve'
    SED_FIT = 'sed_fit', 'SED fit'
    LIGHTCURVE_FIT = 'lightcurve_fit', 'Light curve fit'
    SPECTRAL_FIT = 'spectral_fit', 'Spectral fit'
    CROSS_CORR = 'cross_corr', 'Cross correlation'
    GENERIC = 'generic', 'Generic'
    UNKNOWN = 'unknown', 'Unknown'


class CategorySource(models.TextChoices):
    AUTO = 'auto', 'Automatic'
    USER = 'user', 'User'


@dataclass(frozen=True)
class CategoryMeta:
    label: str
    color: str
    data_type: str
    file_type_aliases: frozenset[str]
    derived_parameters: str = ''


CATEGORY_META: dict[str, CategoryMeta] = {
    AnalysisCategory.RV_SOLUTION: CategoryMeta(
        label='RV solution',
        color='#1e88e5',
        data_type=GENERIC,
        file_type_aliases=frozenset({'RV', 'rv', 'rv_solution'}),
    ),
    AnalysisCategory.RV_CURVE: CategoryMeta(
        label='RV curve',
        color='#26a69a',
        data_type=GENERIC,
        file_type_aliases=frozenset({'RC', 'rv_curve', 'rvcurve'}),
    ),
    AnalysisCategory.SED_FIT: CategoryMeta(
        label='SED fit',
        color='#8e24aa',
        data_type=SED,
        file_type_aliases=frozenset({'SF', 'sedfit', 'SED', 'sed_fit'}),
        derived_parameters='',
    ),
    AnalysisCategory.LIGHTCURVE_FIT: CategoryMeta(
        label='Light curve fit',
        color='#43a047',
        data_type=GENERIC,
        file_type_aliases=frozenset({'LC', 'LF', 'lc', 'lightcurve', 'lightcurve_fit'}),
    ),
    AnalysisCategory.SPECTRAL_FIT: CategoryMeta(
        label='Spectral fit',
        color='#fb8c00',
        data_type=GENERIC,
        file_type_aliases=frozenset({'XF', 'spectral', 'spectral_fit'}),
    ),
    AnalysisCategory.CROSS_CORR: CategoryMeta(
        label='Cross correlation',
        color='#00897b',
        data_type=GENERIC,
        file_type_aliases=frozenset({'CC', 'cross_corr', 'crosscorr'}),
    ),
    AnalysisCategory.GENERIC: CategoryMeta(
        label='Generic',
        color='#546e7a',
        data_type=GENERIC,
        file_type_aliases=frozenset({'??', 'gen', 'generic', 'GF', 'grid', 'grid_fit'}),
    ),
    AnalysisCategory.UNKNOWN: CategoryMeta(
        label='Unknown',
        color='#757575',
        data_type=GENERIC,
        file_type_aliases=frozenset(),
    ),
}

_ALIAS_TO_CATEGORY: dict[str, str] = {}
for code, meta in CATEGORY_META.items():
    for alias in meta.file_type_aliases:
        _ALIAS_TO_CATEGORY[alias.lower()] = code


def resolve_category(file_type: str | None) -> tuple[str, str]:
    """Map HDF5 file type code to (category, category_source)."""
    if not file_type or not str(file_type).strip():
        return AnalysisCategory.UNKNOWN, CategorySource.AUTO

    key = str(file_type).strip().lower()
    if key in _ALIAS_TO_CATEGORY:
        return _ALIAS_TO_CATEGORY[key], CategorySource.AUTO

    if key in CATEGORY_META:
        return key, CategorySource.AUTO

    return AnalysisCategory.UNKNOWN, CategorySource.AUTO


def category_label(code: str | None) -> str:
    if not code:
        return CATEGORY_META[AnalysisCategory.UNKNOWN].label
    meta = CATEGORY_META.get(code)
    return meta.label if meta else code


def category_color(code: str | None) -> str:
    if not code:
        return CATEGORY_META[AnalysisCategory.UNKNOWN].color
    meta = CATEGORY_META.get(code)
    return meta.color if meta else CATEGORY_META[AnalysisCategory.UNKNOWN].color


def category_data_type(code: str | None) -> str:
    if not code:
        return GENERIC
    meta = CATEGORY_META.get(code)
    return meta.data_type if meta else GENERIC


def category_derived_parameters(code: str | None) -> str:
    if not code:
        return ''
    meta = CATEGORY_META.get(code)
    return meta.derived_parameters if meta else ''


def choices_for_api() -> list[dict[str, str]]:
    return [
        {
            'value': code,
            'label': meta.label,
            'color': meta.color,
            'data_type': meta.data_type,
        }
        for code, meta in CATEGORY_META.items()
        if code != AnalysisCategory.UNKNOWN
    ] + [
        {
            'value': AnalysisCategory.UNKNOWN,
            'label': CATEGORY_META[AnalysisCategory.UNKNOWN].label,
            'color': CATEGORY_META[AnalysisCategory.UNKNOWN].color,
            'data_type': CATEGORY_META[AnalysisCategory.UNKNOWN].data_type,
        },
    ]


def valid_category_codes() -> Iterable[str]:
    return CATEGORY_META.keys()
