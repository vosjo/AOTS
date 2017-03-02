
from astropy.coordinates.angles import Angle

#==============================================================================================
# BASIC  INFORMATION extraction
#==============================================================================================

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
   
   return systemname, ra, dec, name, note, atype

def basic_info_sedfit(data):
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
   
   return systemname, ra, dec, name, '', 'sedfit'


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
   
   if 'results' in data and ('igrid_search' in data['results'] or 'iminimize' in data['results']):
      return basic_info_sedfit(data)
   
   else:
      return basic_info_generic(data)

#==============================================================================================
# PARAMETER extraction
#==============================================================================================

def get_parameters_sedfit(data):
   """
   Returns a dictionary with all parameters containing the value, error (upper and lower) and unit,
   based on the confidence intervals included in the igrid_search or iminimize results.
   
   returns: 
   { parname: [value, error_l, error_u, unit],}
   """
   
   if not 'iminimize' in data['results'] and not 'igrid_search' in data['results']:
      return {}
   
   ci = data['results']['iminimize']['CI'] if 'iminimize' in data['results'] else data['results']['igrid_search']['CI']
   
   parameters2 = [('teff', 'K'), ('logg', 'dex'), ('rad', 'Rsol'), ('z', 'dex')]
   parameters1 = [('ebv', '')]
   upper, lower = '_u', '_l'
   
   results = {}
   for (p, u) in parameters1:
      results[p] = [ci[p], ci[p+upper] - ci[p], ci[p] - ci[p+lower], u]
      
   for (p, u) in parameters2:
      results[p+'1'] = [ci[p], ci[p+upper] - ci[p], ci[p] - ci[p+lower], u]
      p = p+'2'
      results[p] = [ci[p], ci[p+upper] - ci[p], ci[p] - ci[p+lower], u]
   
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
      return get_parameters_sedfit(data)
   
   else:
      return get_parameters_generic(data)