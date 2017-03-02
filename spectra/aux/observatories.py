"""
List of Observatory information
"""
import ephem

def get_observatory(telescope):
   """
   Returns a ephem Observer object based on the telescope name
   """
   if telescope == 'ESO-VLT-U2':
      return vlt()
   elif telescope == 'MPI-2.2':
      return mpg22()
   elif telescope == 'Mercator':
      return mercator()
   else:
      return ephem.Observer()

def vlt():
   """
   UT1 - UT4 at ESO Paranal observatory
   """
   observatory = ephem.Observer()
   observatory.lon = '-70:24:15'
   observatory.lat = '-24:37:38'
   observatory.elevation = 2635
   
   return observatory

def mercator():
   """
   Mercator telescope at La Palma (ES)
   """
   observatory = ephem.Observer()
   observatory.lon = '17:52:42'
   observatory.lat = '28:45:44'
   observatory.elevation = 2333
   
   return observatory

def ntt():
   """
   NTT telescope at La Silla
   """
   observatory = ephem.Observer()
   observatory.lon = '-70:44:01.5'
   observatory.lat = '-29:15:32.1'
   observatory.elevation = 2375
   
   return observatory

def mpg22():
   """
   The MPG 2.2m  telescope at La Silla
   """
   observatory = ephem.Observer()
   observatory.lon = '-70:44:4.543'
   observatory.lat = '-29:15:15.433'
   observatory.elevation = 2335
   
   return observatory