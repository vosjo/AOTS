import numpy as np

from analysis.services.parameter_sources import get_or_create_avg_source


def calculate_average(params):
    """
    Calculates the average value and error based on the given parameters.
    params needs to be a queryset.
    """
    values = np.array(params.values_list('value', flat=True))

    errors_l = np.array(params.values_list('error_l', flat=True))
    errors_u = np.array(params.values_list('error_u', flat=True))
    errors = (errors_l + errors_u) / 2.0

    errors = np.where(errors == 0, values / 10., errors)
    errors = np.where(errors == 0, 1., errors)

    error = np.sqrt(np.sum(errors ** 2)) / len(errors)

    return np.average(values, weights=1. / errors), error


def delete_orphan_average(param):
    from analysis.models.parameters import Parameter
    try:
        ap = Parameter.objects.get(
            name__exact=param.name,
            component__exact=param.component,
            star__exact=param.star,
            valid__exact=True,
            average__exact=True,
        )
        ap.delete()
    except Parameter.DoesNotExist:
        pass


def sync_average_for(param):
    """
    Create, update, or delete the average parameter for a non-average parameter.
    """
    from analysis.models.parameters import Parameter
    from stars.models import Star
    if param.average:
        return

    try:
        param.star
    except Star.DoesNotExist:
        return

    sources = Parameter.objects.filter(
        name__exact=param.name,
        component__exact=param.component,
        star__exact=param.star,
        valid__exact=True,
        average__exact=False,
    )

    if not sources.exists():
        delete_orphan_average(param)
        return

    value, error = calculate_average(sources)

    try:
        ap = Parameter.objects.get(
            name__exact=param.name,
            component__exact=param.component,
            star__exact=param.star,
            valid__exact=True,
            average__exact=True,
        )
        ap.value = value
        ap.error = error
        ap.save()
    except Parameter.DoesNotExist:
        ds = get_or_create_avg_source(param.star.project)
        Parameter.objects.create(
            star=param.star,
            name=param.name,
            component=param.component,
            value=value,
            error=error,
            unit=param.unit,
            average=True,
            valid=True,
            parameter_source=ds,
        )


def sync_averages_for_star(star):
    """Ensure average rows exist for all valid non-average parameters on a star."""
    from analysis.models.parameters import Parameter
    seen = set()
    for param in Parameter.objects.filter(star=star, average=False, valid=True):
        key = (param.name.lower(), param.component)
        if key in seen:
            continue
        seen.add(key)
        sync_average_for(param)
