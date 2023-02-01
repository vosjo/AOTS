from astropy.coordinates.angles import Angle
from astropy import units as u
from analysis.models import DEFAULT_PARAMETERS, PARAMETER_ALIASES, \
                            UNIT_ALIASES

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
             - type code of analysis method: 'RV', 'SF', 'GF', 'XF', '??'
    """

    if ('results' in data and ('igrid_search' in data['results'] or 'iminimize' in data['results'])) or (
            'master' in data):
        return basic_info_special_sedfit(data)

    else:
        return basic_info_generic(data)


# ==============================================================================================
# PARAMETER extraction
# ==============================================================================================

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
    for default_unit, aliases in UNIT_ALIASES.items():
        if unit in aliases:
            return default_unit
    else:
        return unit


def parameter_homogenisation(data):
    '''
        This function ensures that parameters are save with default names
        and units. Non default units or names will be converted, if possible.

        Parameters
        ----------
            data            : dictionary`
                Dictionary with input parameters

        Returns
        -------
            results         : dictionary`
                Dictionary with default parameter names and units
    '''
    results = {}
    for pname, parameter in data.items():
        #   Check if parameter name is a default one or not
        if pname in DEFAULT_PARAMETERS.keys():
            parameter_name = pname
        else:
            for default_name, aliases in PARAMETER_ALIASES.items():
                if pname in aliases:
                    parameter_name = default_name
                    break
            else:
                return results

        #   Add to results
        results[parameter_name] = parameter

        #   Find units
        default_unit = DEFAULT_PARAMETERS[parameter_name]
        parameter_unit = unit_homogenisation(parameter['unit'], parameter_name)
        results[parameter_name]['unit'] = parameter_unit

        if default_unit != parameter_unit:
            #   Convert value and error if unit mismatch
            try:
                value = parameter['value'] * u.Unit(parameter_unit)
                if 'err_l' in parameter:
                    err_l = parameter['err_l'] * u.Unit(parameter_unit)
                else:
                    err_l = parameter['err'] * u.Unit(parameter_unit)
                if 'err_u' in parameter:
                    err_u = parameter['err_u'] * u.Unit(parameter_unit)
                else:
                    err_u = parameter['err'] * u.Unit(parameter_unit)
                    results[parameter_name].pop('err')

                #   Actual conversion
                converted_value = value.to_value(u.Unit(default_unit))
                results[parameter_name]['value'] = converted_value
                converted_err_l = err_l.to_value(u.Unit(default_unit))
                results[parameter_name]['err_l'] = converted_err_l
                converted_err_u = err_u.to_value(u.Unit(default_unit))
                results[parameter_name]['err_u'] = converted_err_u

                results[parameter_name]['unit'] = default_unit
            except:
                results.pop(parameter_name)

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

    parameters1 = [('ebv', '')]
    parameters2 = [('teff', 'K'), ('logg', 'dex'), ]
    upper, lower = '_u', '_l'

    results = {}
    for (p, u) in parameters1:
        results[p] = [ci[p], ci[p + upper] - ci[p], ci[p] - ci[p + lower], u]

    for (p, u) in parameters2:
        results[p + '1'] = [ci[p], ci[p + upper] - ci[p], ci[p] - ci[p + lower], u]
        p = p + '2'
        results[p] = [ci[p], ci[p + upper] - ci[p], ci[p] - ci[p + lower], u]

    #   Check parameter names and units
    results = parameter_homogenisation(results)

    return results


def get_parameters_generic(data):
    """
    Returns a dictionary with all parameters containing the value, error (upper and lower) and unit,
    will read both one error and an upper and lower limit

    returns:
    { parname: [value, error_l, error_u, unit],}
    """
    if not 'PARAMETERS' in data:
        return {}

    pars = data['PARAMETERS']

    #   Check parameter names and units
    pars = parameter_homogenisation(pars)

    results = {}
    for pname, parameter in pars.items():
        value = parameter['value']
        unit = parameter['unit']
        err_l = parameter['err_l'] if 'err_l' in parameter else parameter['err']
        err_u = parameter['err_u'] if 'err_u' in parameter else parameter['err']
        results[pname] = [value, err_l, err_u, unit]

    return results


def get_parameters(data):
    """
    Returns a dictionary with all parameters containing the value, error (upper and lower) and unit

    returns:
    { parname: [value, error_l, error_u, unit],}
    """

    if 'results' in data and ('igrid_search' in data['results'] or 'iminimize' in data['results']):
        return get_parameters_special_sedfit(data)

    else:
        return get_parameters_generic(data)
