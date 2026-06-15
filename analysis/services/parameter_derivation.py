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
