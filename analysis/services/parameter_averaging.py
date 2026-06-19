"""
Weighted-mean helper and deprecated wrappers around consensus cache sync.

New code should use ``analysis.services.parameter_consensus``.
"""

import warnings


def calculate_average(params):
    """
    Calculates the average value and error based on the given parameters.
    params needs to be a queryset.
    """
    import numpy as np

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
    from analysis.services import parameter_io

    try:
        ap = Parameter.objects.get(
            name__exact=param.name,
            component__exact=param.component,
            star__exact=param.star,
            valid__exact=True,
            average__exact=True,
            derivedparameter__isnull=True,
        )
        parameter_io.delete_measurement(ap)
    except Parameter.DoesNotExist:
        pass


def sync_average_for(param):
    """Deprecated: use ``parameter_consensus.sync_consensus_cache``."""
    from analysis.services.parameter_consensus import sync_consensus_cache

    warnings.warn(
        'sync_average_for is deprecated; use parameter_consensus.sync_consensus_cache',
        DeprecationWarning,
        stacklevel=2,
    )
    if param.average:
        return
    try:
        param.star
    except Exception:
        return
    sync_consensus_cache(param.star, param.name, param.component)


def sync_averages_for_star(star):
    """Deprecated: use ``parameter_consensus.sync_consensus_for_star``."""
    from analysis.services.parameter_consensus import sync_consensus_for_star

    warnings.warn(
        'sync_averages_for_star is deprecated; use parameter_consensus.sync_consensus_for_star',
        DeprecationWarning,
        stacklevel=2,
    )
    sync_consensus_for_star(star)
