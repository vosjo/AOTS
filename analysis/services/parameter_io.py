"""Explicit write API for Parameter / DerivedParameter (replaces Django signal bookkeeping)."""

from __future__ import annotations

from analysis.models.parameters import DerivedParameter, Parameter, combine_parameter_name
from analysis.services.parameter_consensus import (
    consensus_queryset,
    sync_consensus_cache,
    sync_consensus_for_star,
)
from analysis.services.parameter_derivation import (
    refresh_derived_for,
    setup_derived_on_create,
)
from analysis.services.parameter_sources import get_or_create_avg_source


def apply_cname(param) -> None:
    param.cname = combine_parameter_name(param.name, param.component)


def after_measurement_saved(param) -> None:
    """Sync consensus cache row and refresh dependent derived parameters."""
    if param.average:
        if param.derived_parameters.exists():
            refresh_derived_for(param)
        return
    sync_consensus_cache(param.star, param.name, param.component)
    if param.derived_parameters.exists():
        refresh_derived_for(param)


def after_measurement_deleted(param, *, derived_pks=()) -> None:
    if param.average:
        if derived_pks:
            DerivedParameter.objects.filter(pk__in=derived_pks).delete()
        return
    sync_consensus_cache(param.star, param.name, param.component)
    if derived_pks:
        DerivedParameter.objects.filter(pk__in=derived_pks).delete()


def after_star_parameters_batch(star) -> None:
    """Run after bulk parameter creates/updates for one star (scripts, ingestion)."""
    sync_consensus_for_star(star)
    for param in consensus_queryset(star=star):
        if param.derived_parameters.exists():
            refresh_derived_for(param)


def create_measurement(
    *,
    star,
    name,
    component=0,
    value=0.0,
    error_l=0.0,
    error_u=0.0,
    unit='',
    valid=True,
    average=False,
    analysis=None,
    parameter_source=None,
    run_after=True,
) -> Parameter:
    param = Parameter(
        star=star,
        name=name,
        component=component,
        value=value,
        error_l=error_l,
        error_u=error_u,
        unit=unit,
        valid=valid,
        average=average,
        analysis=analysis,
        parameter_source=parameter_source,
    )
    param.save()
    if run_after:
        after_measurement_saved(param)
    return param


def update_measurement(param, run_after=True, **fields) -> Parameter:
    for key, val in fields.items():
        setattr(param, key, val)
    param.save()
    if run_after:
        after_measurement_saved(param)
    return param


def delete_measurement(param, run_after=True) -> None:
    derived_pks = []
    if param.pk:
        derived_pks = list(param.derived_parameters.values_list('pk', flat=True))
    param.delete()
    if run_after:
        after_measurement_deleted(param, derived_pks=derived_pks)


def replace_measurement(param, run_after=True, **fields) -> Parameter:
    star = param.star
    defaults = {
        'name': param.name,
        'component': param.component,
        'unit': param.unit,
        'analysis': param.analysis,
        'parameter_source': param.parameter_source,
        'value': param.value,
        'error_l': param.error_l,
        'error_u': param.error_u,
        'valid': param.valid,
        'average': param.average,
    }
    defaults.update(fields)
    delete_measurement(param, run_after=False)
    return create_measurement(star=star, run_after=run_after, **defaults)


def create_derived_record(*, star, project, name, component) -> DerivedParameter | None:
    """Create a derived parameter row and calculate it (no signals)."""
    if DerivedParameter.objects.filter(
        star=star,
        name=name,
        component=component,
        average=True,
    ).exists():
        return None

    avg_source = get_or_create_avg_source(project)
    dpar = DerivedParameter(
        star=star,
        name=name,
        component=component,
        average=True,
        parameter_source=avg_source,
    )
    dpar.save()
    if setup_derived_on_create(dpar):
        dpar.save(update_fields=['value', 'error_l', 'error_u', 'unit', 'average', 'cname'])
        return dpar
    dpar.delete()
    return None
