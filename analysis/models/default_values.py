import numpy as np

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
    'met': 2,
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

#   Default parameters and corresponding default units
DEFAULT_PARAMETERS = {
    'e': '',
    'k1': 'km/s',
    'k2': 'km/s',
    'omega': '',
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
    }

#   Parameter aliases
PARAMETER_ALIASES = {
    # 'L': ['L*', 'Lstar'],         #   Example
    'v01': ['v', 'v0'],
    'k1': ['k'],
    }

#   Unit aliases
UNIT_ALIASES = {
    'solRad' : ['Rsol'],
    'solLum' : ['Lsol'],
    }

def split_parameter_name(name):
    if name[-1] in ['0', '1', '2']:
        component = int(name[-1])
        name = name[:-1]
    else:
        name = name
        component = 0
    return name, component


def round_value(value, name=None, error=None):
    """
    Rounds a value based on the parameter name
    """

    # try to round based on the number of significant digits in the error if possible
    if not error is None and error != 0:
        sd = -1 * np.floor(np.log10(abs(error))) + 1
        value = np.round(value, int(sd))

        if sd <= 0:
            return int(value)
        else:
            return value

    # else round based on the type of parameter
    if not name is None:
        name, component = split_parameter_name(name)

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
    'met': 14,
    'vmicro': 15,
    'vrot': 16,
    'dilution': 17,
}


def parameter_order(name):
    """
    returns the parameter order based on its name
    """
    if name in PARAMETER_ORDER:
        return PARAMETER_ORDER[name]
    else:
        return 20
