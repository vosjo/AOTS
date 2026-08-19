import numpy as np

from analysis.parameter_aliases import STORED_PARAMETER_ALIASES, stored_parameter_lookup_names

# -- Method related constants
GENERIC = 'gen'
SED = 'sed'
PLOT_CHOISES = (
    (GENERIC, 'Generic'),
    (SED, 'SED hdf5'),)

# -- PARAMETER related constants

SYSTEM = 0
PRIMARY = 1
SECONDARY = 2
CBDISK = 5
COMPONENT_CHOICES = (
    (SYSTEM, 'System'),
    (PRIMARY, 'Primary'),
    (SECONDARY, 'Secondary'),
    (CBDISK, 'Circumbinary Disk'),)

# SYSTEM_PARAMETERS = ['p', 't0', 'e', 'omega', 'ebv']
STELLAR_PARAMETERS = [PRIMARY, SECONDARY]

# -- PARAMETER rounding
PARAMETER_DECIMALS = {
    'teff': 0,
    'logg': 2,
    'rad': 2,
    'ebv': 3,
    'z': 2,
    'vmicro': 1,
    'vrot': 0,
    'dilution': 2,
    'p': 3,
    't0': 3,
    'e': 3,
    'omega': 2,
    'K': 2,
    'v0': 2,
}

#   Derived parameter base names (display metadata in parameter_labels.py)
DERIVED_PARAMETER_NAMES = ('q', 'msini', 'asini', 'r', 'm')

#   Default parameters and corresponding default units
DEFAULT_PARAMETERS = {
    'e': '',
    'k1': 'km/s',
    'k2': 'km/s',
    'omega': 'deg',
    'p': 'd',
    't0': 'd',
    'v01': 'km/s',
    'v02': 'km/s',
    'L': 'solLum',
    'd': 'pc',
    'ebv': 'mag',
    'rad': 'solRad',
    'teff': 'K',
    'logg': 'dex',
    'z': 'dex',
    'vmicro': 'km/s',
    'vrot': 'km/s',
    'dilution': '',
}

#   Parameter aliases
PARAMETER_ALIASES = {
    # 'L': ['L*', 'Lstar'],         #   Example
    'v01': ['v', 'v0'],
    'k1': ['k'],
    't0': ['t'],
    'logg': ['log_g'],
    'z': ['met'],
}

#   Unit aliases
UNIT_ALIASES = {
    'solRad': ['Rsol'],
    'solLum': ['Lsol'],
}


def canonical_parameter_base(name: str) -> str:
    """Map legacy/alias parameter names to their canonical base (e.g. ``met`` → ``z``)."""
    base, _component = split_parameter_name(name)
    if base in DEFAULT_PARAMETERS or base in PARAMETER_DECIMALS or base in PARAMETER_ORDER:
        return base
    for canonical, aliases in PARAMETER_ALIASES.items():
        canonical_base, _ = split_parameter_name(canonical)
        if base.lower() == canonical_base.lower():
            return canonical_base
        if base.lower() in (alias.lower() for alias in aliases):
            return canonical_base
    return base


def split_parameter_name(name):
    # Epoch T0 is a single parameter name; trailing 0 is not a component suffix.
    if name.lower() == 't0':
        return 't0', 0
    if name[-1] in ['0', '1', '2']:
        component = int(name[-1])
        name = name[:-1]
    else:
        component = 0
    return name, component


def round_value(value, name=None, error=None):
    """
    Rounds a value based on the parameter name
    """

    # try to round based on the number of significant digits in the error if possible
    if error is not None and error != 0:
        sd = -1 * np.floor(np.log10(abs(error))) + 1
        value = np.round(value, int(sd))

        if sd <= 0:
            return int(value)
        else:
            return value

    # else round based on the type of parameter
    if name is not None:
        name, component = split_parameter_name(name)
        name = canonical_parameter_base(name)

        decimals = PARAMETER_DECIMALS.get(name, 3)
        if decimals > 0:
            return np.round(value, decimals)
        else:
            return int(value)

    # is no name or error is given, round to 3 decimals by default
    return np.round(value, 3)


# -- PARAMETER sorting
PARAMETER_ORDER = {
    'p': 0,
    't0': 1,
    'e': 2,
    'omega': 3,
    'K': 4,
    'v0': 5,

    'teff': 10,
    'logg': 11,
    'rad': 12,
    'ebv': 13,
    'z': 14,
    'vmicro': 15,
    'vrot': 16,
    'dilution': 17,
}


def parameter_order(name):
    """
    returns the parameter order based on its name
    """
    base = canonical_parameter_base(name)
    if base in PARAMETER_ORDER:
        return PARAMETER_ORDER[base]
    else:
        return 20
