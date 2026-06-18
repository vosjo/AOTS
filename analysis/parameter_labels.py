"""
Human-readable names and units for analysis parameters.

Storage units (e.g. solRad, Msol) stay unchanged in the database; use the helpers
here whenever values are shown in the UI or plots.
"""
from __future__ import annotations

from analysis.models.default_values import (
    DEFAULT_PARAMETERS,
    PARAMETER_ALIASES,
    STORED_PARAMETER_ALIASES,
    UNIT_ALIASES,
    split_parameter_name,
)

# Base parameter names (keys in DEFAULT_PARAMETERS use k1/v01 aliases; lookup uses
# normalized names after split_parameter_name).
PARAMETER_DISPLAY: dict[str, str] = {
    'e': 'Eccentricity e',
    'k': 'Semiamplitude K',
    'omega': 'Argument of periastron ω',
    'p': 'Orbital period P',
    't0': 'Epoch T₀',
    'v0': 'Systemic velocity γ',
    'L': 'Luminosity L',
    'd': 'Distance d',
    'ebv': 'Reddening E(B-V)',
    'rad': 'Radius R',
    'teff': 'Effective temperature T_eff',
    'logg': 'Surface gravity log g',
    'z': 'Metallicity [Fe/H]',
    'vmicro': 'Microturbulent velocity v_micro',
    'vrot': 'Rotational velocity v sin i',
    'dilution': 'Light dilution factor',
    # Project-average parameters outside DEFAULT_PARAMETERS
    'parallax': 'Parallax',
    'pmdec': 'Proper motion (Dec.)',
    'pmra': 'Proper motion (RA)',
    # Gaia / photometry-related parameters
    'absolute_g_mag': 'Absolute G-Band Magnitude',
    'mag': 'G-Band Magnitude',
    'bp_rp': 'BP-RP Color',
}

# HRD dashboard column keys (dash/plotting.py); aligned with DB cname where possible.
HRD_AXIS_PARAMETERS: tuple[str, ...] = (
    'teff', 'logg', 'mag', 'absolute_g_mag', 'bp_rp',
)

HRD_AXIS_UNITS: dict[str, str] = {
    'teff': 'K',
    'logg': '',
    'mag': 'mag',
    'absolute_g_mag': 'mag',
    'bp_rp': 'mag',
}

DERIVED_PARAMETER_DISPLAY: dict[str, str] = {
    'q': 'Mass ratio (q)',
    'msini': 'Minimum mass M sin i',
    'asini': 'Projected semi-major axis a sin i',
    'r': 'Radius R',
    'm': 'Mass M',
}

# Storage unit -> display string (Unicode solar symbols for web output).
UNIT_DISPLAY: dict[str, str] = {
    '': '',
    'km/s': 'km/s',
    'd': 'd',
    'solLum': 'L☉',
    'solRad': 'R☉',
    'Lsol': 'L☉',
    'Rsol': 'R☉',
    'Msol': 'M☉',
    'pc': 'pc',
    'mag': 'mag',
    'K': 'K',
    'dex': 'dex',
}

_COMPONENT_SUBSCRIPTS = str.maketrans('012', '₀₁₂')


def parse_cname(cname: str) -> tuple[str, int]:
    """Split combined name (e.g. k_1, msini_2) into base name and component."""
    if '_' in cname:
        base, suffix = cname.rsplit('_', 1)
        if suffix in '012':
            return base, int(suffix)
    return cname, 0


def normalize_parameter_name(name: str) -> str:
    """Map storage/alias names (k1, v01, mag_abs) to canonical base names (k, v0, absolute_g_mag)."""
    base, _component = split_parameter_name(name)
    lowered = base.lower()

    for canonical, aliases in STORED_PARAMETER_ALIASES.items():
        if lowered == canonical.lower():
            return canonical
        for alias in aliases:
            if lowered == alias.lower():
                return canonical

    for canonical, aliases in PARAMETER_ALIASES.items():
        canonical_base, _ = split_parameter_name(canonical)
        if lowered == canonical_base.lower():
            return canonical_base
        for alias in aliases:
            if lowered == alias.lower():
                return canonical_base
    return base


def normalize_hrd_axis_key(axis_key: str) -> str:
    """Map legacy HRD form/plot axis keys to canonical column names."""
    if not axis_key:
        return axis_key
    return normalize_parameter_name(axis_key)


def _component_suffix(component: int) -> str:
    if component in (1, 2):
        return str(component).translate(_COMPONENT_SUBSCRIPTS)
    return ''


def parameter_display_name(name: str, component: int = 0) -> str:
    """Display label for a parameter base name and optional component."""
    base = normalize_parameter_name(name)
    label = (
        DERIVED_PARAMETER_DISPLAY.get(base)
        or DERIVED_PARAMETER_DISPLAY.get(base.lower())
        or PARAMETER_DISPLAY.get(base)
        or PARAMETER_DISPLAY.get(base.lower())
        or base
    )
    suffix = _component_suffix(component)
    return f'{label}{suffix}' if suffix else label


def cname_display_label(cname: str) -> str:
    """Display label for a stored combined parameter name (cname)."""
    base, component = parse_cname(cname)
    return parameter_display_name(base, component)


def unit_display_name(unit: str | None) -> str:
    """Format a stored unit string for display."""
    if not unit:
        return ''
    if unit in UNIT_DISPLAY:
        return UNIT_DISPLAY[unit]
    for canonical, aliases in UNIT_ALIASES.items():
        if unit == canonical or unit in aliases:
            return UNIT_DISPLAY.get(canonical, canonical)
    return unit


def parameter_label_with_unit(
    name_or_cname: str,
    unit: str | None = None,
    *,
    from_cname: bool = False,
) -> str:
    """Full label for selects/tables, e.g. 'Orbital period P [d]'."""
    if from_cname:
        label = cname_display_label(name_or_cname)
    else:
        base, component = parse_cname(name_or_cname)
        if base == name_or_cname and '_' not in name_or_cname:
            base, component = split_parameter_name(name_or_cname)
        label = parameter_display_name(base, component)

    unit_label = unit_display_name(unit)
    if unit_label:
        return f'{label} [{unit_label}]'
    return label


def parameter_axis_label(cname: str, unit: str | None = None) -> str:
    """Axis title for plots (same as parameter_label_with_unit)."""
    return parameter_label_with_unit(cname, unit, from_cname=True)


def hrd_axis_label(axis_key: str) -> str:
    """Axis / legend label for the dashboard HRD plot."""
    canonical = normalize_hrd_axis_key(axis_key)
    unit = HRD_AXIS_UNITS.get(canonical)
    return parameter_label_with_unit(canonical, unit or None)


def hrd_axis_choices() -> list[tuple[str, str]]:
    """Value/label pairs for HRD plotter form selects."""
    return [(key, hrd_axis_label(key)) for key in HRD_AXIS_PARAMETERS]


def hrd_axis_labeldict() -> dict[str, str]:
    """Mapping of HRD axis keys to full labels (replaces legacy dash.labels.labeldict)."""
    return {key: hrd_axis_label(key) for key in HRD_AXIS_PARAMETERS}


def default_unit_display_for_name(name: str) -> str:
    """Default unit display for a parameter name key in DEFAULT_PARAMETERS."""
    base, _ = split_parameter_name(name)
    for key, unit in DEFAULT_PARAMETERS.items():
        key_base, _ = split_parameter_name(key)
        if key_base.lower() == base.lower() or key.lower() == name.lower():
            return unit_display_name(unit)
    return ''
