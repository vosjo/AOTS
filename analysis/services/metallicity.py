"""Canonical metallicity storage: parameter ``z`` as [Fe/H] in dex."""

from __future__ import annotations

import numpy as np

CANONICAL_METALLICITY_UNIT = 'dex'
ZSUN = 0.0122

FEH_UNIT_ALIASES = frozenset({
    'dex',
    '[fe/h]',
    'fe/h',
    'feh',
})

Z_MASS_FRACTION_UNIT_ALIASES = frozenset({
    'z',
    'zsun',
    'z_sun',
    'mass_fraction',
    'mass fraction',
    'massfraction',
})


def convert_z_to_feh_dex(z: float, *, z_sun: float = ZSUN) -> float:
    """Convert mass-fraction Z to [Fe/H] in dex (Bertelli et al. 1994)."""
    return float(np.log10(z / z_sun) / 0.977)


def metallicity_unit_kind(unit: str | None) -> str:
    """
    Classify an input unit as ``feh_dex`` ([Fe/H] in dex) or ``z_mass`` (mass fraction).

    Empty unit is treated as [Fe/H] in dex (legacy SED-fit convention).
    """
    normalized = (unit or '').strip().lower()
    if normalized in FEH_UNIT_ALIASES:
        return 'feh_dex'
    if normalized in Z_MASS_FRACTION_UNIT_ALIASES:
        return 'z_mass'
    raise ValueError(f'Unsupported metallicity unit: {unit!r}')


def metallicity_to_feh_dex(
    value: float,
    err_l: float | None = None,
    err_u: float | None = None,
    *,
    unit: str | None = 'dex',
) -> tuple[float, float, float, str]:
    """Convert metallicity to canonical ``z`` = [Fe/H] in dex."""
    kind = metallicity_unit_kind(unit)
    if kind == 'feh_dex':
        el = float(err_l if err_l is not None else 0.0)
        eu = float(err_u if err_u is not None else el)
        return float(value), el, eu, CANONICAL_METALLICITY_UNIT

    z_val = float(value)
    if z_val <= 0:
        raise ValueError('Mass-fraction metallicity must be positive')

    feh = convert_z_to_feh_dex(z_val)
    el = eu = 0.0
    if err_l is not None and err_l > 0:
        feh_l = convert_z_to_feh_dex(max(z_val - err_l, np.finfo(float).tiny))
        el = feh - feh_l
    if err_u is not None and err_u > 0:
        feh_u = convert_z_to_feh_dex(z_val + err_u)
        eu = feh_u - feh
    return feh, el, eu, CANONICAL_METALLICITY_UNIT
