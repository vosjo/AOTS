from astropy import units as u
from astropy.coordinates.angles import Angle

from analysis.categories import uses_sed_hdf5_reader
from analysis.auxil.rv_hdf5 import get_fit_parameters_dict
from analysis.models.default_values import DEFAULT_PARAMETERS, UNIT_ALIASES
from analysis.services.metallicity import metallicity_to_feh_dex
from analysis.services.parameter_names import (
    resolve_ingest_parameter_name,
    storage_parameter_name,
)


def _default_parameter_unit(base: str, component: int) -> str | None:
    """Look up the canonical unit for a resolved base/component pair."""
    storage_name = storage_parameter_name(base, component)
    if storage_name in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[storage_name]
    if base in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[base]
    return None


# ==============================================================================================
# BASIC  INFORMATION extraction
# ==============================================================================================

def basic_info_generic(data):
    """
    returns info necessary to match the generic analysis dataset with the correct star

    returns: - systemname of the system
             - ra of the system
             - dec of the system
             - name of the analysis method
             - note to analysis method
             - type code of analysis method
    """

    systemname = data.get('systemname', 'UK')

    ra = data.get('ra', 0.0)
    dec = data.get('dec', 0.0)
    if type(ra) == str:
        ra = Angle(ra, unit='hour').degree
    if type(dec) == str:
        dec = Angle(dec, unit='degree').degree

    atype = data.get('type', '??')

    name = data.get('name', 'generic dataformat')

    note = data.get('note', '')

    reference = data.get('reference', '')

    return systemname, ra, dec, name, note, reference, atype


def basic_info_special_sedfit(data):
    """
    returns info necessary to match the SED fit analysis dataset with the correct star

    returns: - name of the system
             - ra of the system
             - dec of the system
             - name of the analysis method
             - possible note added to analysis method
             - type code of analysis method: 'SF'
    """

    info = data['info']
    systemname = info['oname']
    ra = float(info['jradeg'])
    dec = float(info['jdedeg'])

    method = []
    if 'igrid_search' in data['results']:
        method += ['igrid_seach']
    if 'iminimize' in data['results']:
        method += ['iminimize']
    method = ', '.join(method)

    name = 'SED fit of {} using {}'.format(systemname, method)

    return systemname, ra, dec, name, '', '', 'sedfit'


def get_basic_info(data):
    """
    Returns basic info necessary to match the dataset to the correct star, and to
    populate the database object with the name, type and note of the dataset.

    returns: - name of the system
             - ra of the system
             - dec of the system
             - name of the analysis method
             - note added to analysis method
             - type code of analysis method: 'RV', 'RC', 'SF', 'GF', 'XF', '??'
    """

    if uses_sed_hdf5_reader(data):
        return basic_info_special_sedfit(data)

    return basic_info_generic(data)


# ==============================================================================================
# PARAMETER extraction
# ==============================================================================================

def _parameter_record_to_dict(parameter):
    if isinstance(parameter, (list, tuple)):
        value, err_l, err_u, unit = parameter
        return {
            'value': value,
            'err_l': err_l,
            'err_u': err_u,
            'unit': unit,
        }
    record = dict(parameter)
    if 'err_l' not in record and 'err' in record:
        record['err_l'] = record['err']
        record['err_u'] = record['err']
    return record


def _record_to_tuple(record):
    err_l = record['err_l']
    err_u = record['err_u']
    return [record['value'], err_l, err_u, record['unit']]


def unit_homogenisation(unit, parameter_name):
    '''
        This function ensures that the provided unit is compatible with
        the astropy unit modules.

        Parameters
        ----------
        unit                : `string`
            Input unit

        parameter_name      : `string`
            Parameter name. Used to handle special cases, such as no unit given.

        Returns
        -------
                            : `string`
            Default unit
    '''
    if parameter_name == 'ebv' and unit == '':
        return 'mag'
    if parameter_name == 'z' and unit == '':
        return 'dex'
    if parameter_name in ('vmicro', 'vrot') and unit == '':
        return 'km/s'
    if parameter_name == 'omega' and unit == '':
        return 'deg'
    for default_unit, aliases in UNIT_ALIASES.items():
        if unit in aliases:
            return default_unit
    else:
        return unit


def parameter_homogenisation(data):
    '''
        This function ensures that parameters are saved with default names
        and units. Non default units or names will be converted, if possible.

        Parameters
        ----------
            data            : dictionary`
                Dictionary with input parameters

        Returns
        -------
            results         : dictionary`
                Dictionary mapping parameter keys to
                [value, error_l, error_u, unit] lists
    '''
    results = {}
    for pname, raw in data.items():
        resolved = resolve_ingest_parameter_name(pname)
        if resolved is None:
            continue

        base, component = resolved
        storage_name = storage_parameter_name(base, component)
        record = _parameter_record_to_dict(raw)

        default_unit = _default_parameter_unit(base, component)
        if default_unit is None:
            continue
        parameter_unit = unit_homogenisation(record['unit'], base)

        if base == 'z':
            try:
                value, err_l, err_u, parameter_unit = metallicity_to_feh_dex(
                    record['value'],
                    record.get('err_l'),
                    record.get('err_u'),
                    unit=parameter_unit,
                )
                record['value'] = value
                record['err_l'] = err_l
                record['err_u'] = err_u
                record['unit'] = parameter_unit
            except (ValueError, ZeroDivisionError):
                continue
        elif default_unit != parameter_unit:
            try:
                value = record['value'] * u.Unit(parameter_unit)
                err_l = record['err_l'] * u.Unit(parameter_unit)
                err_u = record['err_u'] * u.Unit(parameter_unit)

                record['value'] = value.to_value(u.Unit(default_unit))
                record['err_l'] = err_l.to_value(u.Unit(default_unit))
                record['err_u'] = err_u.to_value(u.Unit(default_unit))
                record['unit'] = default_unit
            except Exception:
                continue
        else:
            record['unit'] = default_unit

        results[storage_name] = _record_to_tuple(record)

    return results


def get_parameters_special_sedfit(data):
    """
    Returns a dictionary with all parameters containing the value, error (upper and lower) and unit,
    based on the confidence intervals included in the igrid_search or iminimize results.

    returns:
    { parname: [value, error_l, error_u, unit],}
    """

    if not 'iminimize' in data['results'] and not 'igrid_search' in data['results']:
        return {}

    ci = data['results']['iminimize']['CI'] if 'iminimize' in data['results'] else data['results']['igrid_search']['CI']

    upper, lower = '_u', '_l'

    def _ci_tuple(key, unit):
        if key not in ci or key + upper not in ci or key + lower not in ci:
            return None
        return [ci[key], ci[key + upper] - ci[key], ci[key] - ci[key + lower], unit]

    def _add_component_pair(base, unit):
        t1 = _ci_tuple(base, unit)
        if t1 is not None:
            results[base + '1'] = t1
        t2 = _ci_tuple(base + '2', unit)
        if t2 is not None:
            results[base + '2'] = t2

    results = {}
    for p, u in [('ebv', 'mag')]:
        t = _ci_tuple(p, u)
        if t is not None:
            results[p] = t

    for p, u in [
        ('teff', 'K'),
        ('logg', 'dex'),
        ('z', 'dex'),
        ('vmicro', 'km/s'),
        ('vrot', 'km/s'),
        ('dilution', ''),
    ]:
        _add_component_pair(p, u)

    return parameter_homogenisation(results)


def get_parameters_generic(data):
    """
    Returns a dictionary with all parameters containing the value, error (upper and lower) and unit,
    will read both one error and an upper and lower limit

    returns:
    { parname: [value, error_l, error_u, unit],}
    """
    from analysis.auxil.rv_hdf5 import is_rv_curve_v2

    if is_rv_curve_v2(data):
        pars = get_fit_parameters_dict(data)
        return parameter_homogenisation(_table_params_to_dict(pars))

    if not 'PARAMETERS' in data:
        return {}

    pars = data['PARAMETERS']
    return parameter_homogenisation(pars)


def _table_params_to_dict(pars: dict) -> dict:
    """Convert astropy table entries from read2dict into plain dicts."""
    out = {}
    for name, raw in pars.items():
        if isinstance(raw, dict):
            out[name] = raw
        elif hasattr(raw, 'dtype') and raw.dtype.names:
            row = raw[0]
            unit = ''
            out[name] = {
                'value': float(row['value']),
                'err_l': float(row['err_l']),
                'err_u': float(row['err_u']),
                'unit': unit,
            }
        else:
            out[name] = raw
    return out


def get_parameters(data):
    """
    Returns a dictionary with all parameters containing the value, error (upper and lower) and unit

    returns:
    { parname: [value, error_l, error_u, unit],}
    """

    if uses_sed_hdf5_reader(data):
        return get_parameters_special_sedfit(data)

    return get_parameters_generic(data)
