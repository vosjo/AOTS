"""
Weighted-mean helper and deprecated wrappers around consensus cache sync.

New code should use ``analysis.services.parameter_consensus``.
"""

import warnings


def calculate_average(params):
    """
    Inverse-variance weighted mean and combined uncertainty.

    For measurements x_i with symmetric uncertainties σ_i = (error_l + error_u) / 2:

        w_i = 1 / σ_i²
        x̄ = Σ(w_i x_i) / Σ(w_i)
        σ_x̄ = 1 / sqrt(Σ w_i)

    Missing uncertainties (σ_i <= 0) fall back to |x_i| / 10, then 1.0, so weights stay finite.
    """
    import numpy as np

    values = np.asarray(params.values_list('value', flat=True), dtype=float)
    errors_l = np.asarray(params.values_list('error_l', flat=True), dtype=float)
    errors_u = np.asarray(params.values_list('error_u', flat=True), dtype=float)
    errors = (errors_l + errors_u) / 2.0

    errors = np.where(errors <= 0, np.abs(values) / 10.0, errors)
    errors = np.where(errors <= 0, 1.0, errors)

    weights = 1.0 / (errors ** 2)
    weight_sum = np.sum(weights)
    if weight_sum == 0:
        return float(np.mean(values)), float(np.mean(errors))

    value = float(np.sum(weights * values) / weight_sum)
    error = float(1.0 / np.sqrt(weight_sum))
    return value, error


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
    if not param.star_id:
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
