
import numpy as np

#-- Method related constants
GENERIC = 'gen'
SED = 'sed'
PLOT_CHOISES = (
   (GENERIC, 'Generic'),
   (SED, 'SED hdf5'),)


#-- PARAMETER related constants

SYSTEM = 0
PRIMARY = 1
SECONDARY = 2
CBDISK = 5
COMPONENT_CHOICES = (
   (SYSTEM, 'System'),
   (PRIMARY,  'Primary'),
   (SECONDARY, 'Secondary'),      
   (CBDISK, 'Circumbinary Disk'),)

#SYSTEM_PARAMETERS = ['p', 't0', 'e', 'omega', 'ebv']
STELLAR_PARAMETERS = [PRIMARY, SECONDARY]

#-- PARAMETER rounding
PARAMETER_DECIMALS = {
   'teff':0, 
   'logg':2, 
   'rad':2, 
   'ebv':3,
   'z':2,
   'met':2,
   'vmicro': 1,
   'vrot':0,
   'dilution':2,
   'p':0, 
   't0':0, 
   'e':3, 
   'omega':2, 
   'K':2, 
   'v0':2,
   }

def round_value(value, name):
   """
   Rounds a value based on the parameter name
   """
   name, component = split_parameter_name(name)
   
   decimals = PARAMETER_DECIMALS.get(name, 3)
   if decimals > 0:
      return np.round(value, decimals)
   else:
      return int(value)

#-- PARAMETER sorting
PARAMETER_ORDER = {
   'p':     0, 
   't0':    1, 
   'e':     2, 
   'omega': 3, 
   'K':     4, 
   'v0':    5,
   
   'teff':    10, 
   'logg':    11, 
   'rad':     12, 
   'ebv':     13,
   'z':       14,
   'met':     14,
   'vmicro':  15,
   'vrot':    16,
   'dilution':17,
   }

def parameter_order(name):
   """
   returns the parameter order based on its name
   """
   if name in PARAMETER_ORDER:
      return PARAMETER_ORDER[name]
   else:
      return 20
