from analysis.auxil import parameter_derivation as derivation_auxil


def find_sources(dpar):
    return derivation_auxil.find_parameters(dpar)


def calculate(dpar):
    return derivation_auxil.calculate(dpar)


def refresh_derived_for(param):
    """Recalculate derived parameters that depend on param."""
    if not param.derived_parameters.exists():
        return
    for derived in param.derived_parameters.all():
        if not derived.update():
            derived.delete()
        else:
            derived.save()


def delete_dependent_derived(param):
    if not param.derived_parameters.exists():
        return
    for derived in param.derived_parameters.all():
        derived.delete()


def setup_derived_on_create(dpar):
    if find_sources(dpar):
        calculate(dpar)
        dpar.average = True
        return True
    return False


def refresh_derived_parameter(dpar):
    """Clear sources, re-link average inputs, and recalculate."""
    dpar.source_parameters.clear()
    if setup_derived_on_create(dpar):
        dpar.save(update_fields=['value', 'error_l', 'error_u', 'unit', 'average', 'cname'])
        return True
    return False


def sync_derived_for_analysis(analysis):
    """
    Create missing and refresh category-derived parameters for an analysis star.
    Returns counts and names that could not be calculated.
    """
    from analysis.auxil.process_analyses import create_derived_parameters
    from analysis.categories import category_derived_parameter_specs, has_category_derived_parameters
    from analysis.models import DerivedParameter

    if not analysis.star_id or not has_category_derived_parameters(analysis.category):
        return {'created': 0, 'updated': 0, 'failed': []}

    from analysis.services.parameter_averaging import sync_averages_for_star
    sync_averages_for_star(analysis.star)

    created = create_derived_parameters(analysis)
    updated = 0
    failed: list[str] = []

    for pname, pcomp in category_derived_parameter_specs(analysis.category):
        label = f'{pname}_{pcomp}' if pcomp else pname
        try:
            dpar = DerivedParameter.objects.get(
                star_id=analysis.star_id,
                name=pname,
                component=pcomp,
                average=True,
            )
        except DerivedParameter.DoesNotExist:
            failed.append(label)
            continue
        if refresh_derived_parameter(dpar):
            updated += 1
        else:
            failed.append(label)

    return {'created': created, 'updated': updated, 'failed': failed}
