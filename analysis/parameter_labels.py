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
    canonical_parameter_base,
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
    'deg': '°',
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


def default_parameter_unit(name: str) -> str | None:
    """Canonical storage unit for a parameter base or cname key."""
    base, component = parse_cname(name)
    if base == name and '_' not in name:
        base, component = split_parameter_name(name)
    base = normalize_parameter_name(base)
    if base in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[base]
    canonical = canonical_parameter_base(base)
    if canonical in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[canonical]
    for key, unit in DEFAULT_PARAMETERS.items():
        key_base, key_component = split_parameter_name(key)
        if canonical_parameter_base(key_base) == canonical and key_component == component:
            return unit
    return None


def effective_parameter_unit(
    name_or_cname: str,
    unit: str | None = None,
    *,
    from_cname: bool = False,
) -> str | None:
    """Stored unit, or canonical default when the database unit is empty."""
    if unit:
        return unit
    if from_cname:
        base, _component = parse_cname(name_or_cname)
    else:
        base, _component = split_parameter_name(name_or_cname)
    return default_parameter_unit(base)


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


PLOTTER_GROUP_ORBIT = 'Orbital parameters'
PLOTTER_GROUP_ASTROMETRY = 'Distance & proper motion'
PLOTTER_GROUP_STELLAR = 'Stellar parameters'

ORBIT_PARAMETER_BASES = frozenset({
    'p', 't0', 'e', 'omega', 'k', 'v0', 'q', 'msini', 'asini',
})

ASTROMETRY_PARAMETER_BASES = frozenset({
    'd', 'parallax', 'pmra', 'pmdec',
})

PLOTTER_PARAMETER_GROUPS = (
    PLOTTER_GROUP_ASTROMETRY,
    PLOTTER_GROUP_ORBIT,
    PLOTTER_GROUP_STELLAR,
)


def _plotter_base_matches(cname: str, bases: frozenset[str]) -> bool:
    base, _ = parse_cname(cname)
    if base == cname and '_' not in cname:
        base, _ = split_parameter_name(cname)
    base = normalize_parameter_name(base)
    lowered = {name.lower() for name in bases}
    return base in bases or base.lower() in lowered


def plotter_parameter_group(cname: str) -> str:
    """Plotter optgroup for a stored consensus cname."""
    if _plotter_base_matches(cname, ORBIT_PARAMETER_BASES):
        return PLOTTER_GROUP_ORBIT
    if _plotter_base_matches(cname, ASTROMETRY_PARAMETER_BASES):
        return PLOTTER_GROUP_ASTROMETRY
    return PLOTTER_GROUP_STELLAR


def group_plotter_parameter_choices(flat_choices: list[tuple[str, str]]) -> list:
    """Group flat plotter (value, label) pairs into Django optgroup choices."""
    grouped: dict[str, list[tuple[str, str]]] = {
        group: [] for group in PLOTTER_PARAMETER_GROUPS
    }
    for value, label in flat_choices:
        grouped[plotter_parameter_group(value)].append((value, label))

    result = []
    for group_name in PLOTTER_PARAMETER_GROUPS:
        options = sorted(grouped[group_name], key=lambda item: item[1].lower())
        if options:
            result.append((group_name, options))
    return result


def group_consensus_parameter_choices(flat_choices: list[tuple[str, str]]) -> list:
    """Group policy parameter choices; wildcard ``*`` stays ungrouped first."""
    wildcard = None
    rest: list[tuple[str, str]] = []
    for value, label in flat_choices:
        if value == '*':
            wildcard = (value, label)
        else:
            rest.append((value, label))

    result = []
    if wildcard:
        result.append(wildcard)
    result.extend(group_plotter_parameter_choices(rest))
    return result


def flatten_plotter_choices(choices) -> list[str]:
    """All option values from flat or grouped Django form choices."""
    values: list[str] = []
    for entry in choices:
        if (
            isinstance(entry, (list, tuple))
            and len(entry) == 2
            and isinstance(entry[1], (list, tuple))
            and entry[1]
            and isinstance(entry[1][0], (list, tuple))
        ):
            values.extend(value for value, _label in entry[1])
        else:
            values.append(entry[0])
    return values


def serialize_plotter_choices(choices) -> list[dict]:
    """JSON-friendly grouped choices for the SPA plotter API."""
    serialized: list[dict] = []
    for entry in choices:
        if (
            isinstance(entry, (list, tuple))
            and len(entry) == 2
            and isinstance(entry[1], (list, tuple))
            and entry[1]
            and isinstance(entry[1][0], (list, tuple))
        ):
            serialized.append({
                'group': entry[0],
                'options': [
                    {'value': value, 'label': label}
                    for value, label in entry[1]
                ],
            })
        else:
            serialized.append({'value': entry[0], 'label': entry[1]})
    return serialized
