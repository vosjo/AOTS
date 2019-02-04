""" 
Functions to derive essential information from the header in instrument specific cases.
"""

import numpy as np
from astropy.time import Time
from observations.models import Spectrum, Observatory

import astropy.units as u
from astropy.coordinates import EarthLocation


def extract_header_info(header):
   """
   Reads the important header information and returns it as a dictionary
   """
   
   if header.get('INSTRUME', '') == 'UVES':
      return derive_uves_info(header)
   elif header.get('INSTRUME', '') == 'FEROS':
      return derive_feros_info(header)
   elif header.get('INSTRUME', '') == 'HERMES':
      return derive_hermes_info(header)
   elif 'SDSS' in header.get('TELESCOP', ''):
      return derive_SDSS_info(header)
   else:
      return derive_generic_info(header)
   
def get_observatory(header, project):
   """
   Finds a suitable observatory or if not possible, create a new one.
   """
   
   d = 0.1  # a difference of 0.1 degree in latitude and longitude is roughly 10 km
   
   #-- try to find the observatory on name match
   if 'TELESCOP' in header:
      try:
         obs = Observatory.objects.get(telescopes__icontains = header['TELESCOP'], project__exact = project)
         return obs
      except Exception as e:
         telescope = header.get('TELESCOP', 'UK')
   
   #-- try to find observatory on location match
   if 'OBSGEO-X' in header:
      x, y, z = header.get('OBSGEO-X', 0), header.get('OBSGEO-Y', 0), header.get('OBSGEO-Z', 0)
      loc = EarthLocation.from_geocentric(x=x*u.m, y=y*u.m, z=z*u.m,)
   elif 'ESO TEL GEOLAT' in header:
      lat, lon, alt = header.get('ESO TEL GEOLAT', 0), header.get('ESO TEL GEOLON', 0), header.get('ESO TEL GEOELEV', 0)
      loc = EarthLocation.from_geodetic(lat=lat*u.deg, lon=lon*u.deg, height=alt*u.m,)
   else:
      loc = EarthLocation.from_geodetic(lat=0*u.deg, lon=0*u.deg, height=0*u.m,)
   
   #-- we look for an observatory that is within 1 degree from location stored in the header, altitude is not checked.
   obs = Observatory.objects.filter(latitude__range = (loc.lat.degree-d, loc.lat.degree+d), 
                                    longitude__range = (loc.lon.degree-d, loc.lon.degree+d),
                                    project__exact = project)
   
   if len(obs) > 0:
      return obs[0]
      

   #-- if still no observatory exists, create a new one.
   obs = Observatory(name=telescope, latitude=loc.lat.degree, longitude=loc.lon.degree,
                     altitude=loc.height.value, project=project)
   obs.save()
      
   return obs
   

def derive_generic_info(header):
   """
   Tries to read some basic information from a unknown spectrum
   
   This information is stored in the spectrum database entry
   """
   
   data = {}
   
   # HJD
   if 'HJD' in header:
      data['hjd'] = header['HJD']
   if 'BJD' in header:
      data['hjd'] = header['BJD']
   else:
      data['hjd'] = 2400000
   
   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = header.get('RA', -1)
   data['dec'] = header.get('DEC', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   
   data['filetype'] = 'UK'
   
   return data


def derive_uves_info(header):
   """
   Reads information from a UVES spectrum
   
   This information is stored in the spectrum database entry
   """
   
   data = {}
   
   # HJD
   data['hjd'] = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd
   
   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = header.get('RA', -1)
   data['dec'] = header.get('DEC', -1)
   data['alt'] = header.get('ESO TEL ALT', -1)
   data['az'] = header.get('ESO TEL AZ', -1)
   data['airmass'] = header.get('ESO TEL AIRM END', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['barycor'] = header.get('ESO QC VRAD BARYCOR', -1)
   data['observer'] = header.get('OBSERVER', 'UK')
   data['filetype'] = header['PIPEFILE']
   
   # observing conditions
   data['wind_speed'] = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   data['wind_direction'] = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   
   return data


def derive_feros_info(header):
   """
   Read header information from a FEROS spectrum
   
   This information is stored in the spectrum database entry
   """
   
   data = {}
   
   # HJD
   data['hjd'] = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd
   
   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = header.get('RA', -1)
   data['dec'] = header.get('DEC', -1)
   data['alt'] = header.get('ESO TEL ALT', -1)
   data['az'] = header.get('ESO TEL AZ', -1)
   data['airmass'] = header.get('ESO TEL AIRM END', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['barycor'] = -1
   data['observer'] = header.get('OBSERVER', 'UK')
   data['filetype'] = header['PIPEFILE']
   
   # observing conditions
   data['wind_speed'] = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   data['wind_direction'] = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   
   return data
   
   

def derive_hermes_info(header):
   """
   Read header information from a HERMES spectrum
   
   This information is stored in the spectrum database entry
   """
   
   data = {}
   
   # HJD
   data['hjd'] = header.get('BJD', 2400000)
   
   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = float(header.get('RA', -1))
   data['dec'] = float(header.get('DEC', -1))
   data['alt'] = float(header.get('TELALT', -1))
   data['az'] = float(header.get('TELAZI', -1))
   data['airmass'] = -1
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['barycor'] = header.get('BVCOR', -1)
   data['observer'] = header.get('OBSERVER', 'UK')
   data['filetype'] = 'MERGE_REBIN'
   
   return data


def derive_SDSS_info(header):
   """
   Read header information from an SDSS spectrum
   
   This information is stored in the spectrum database entry
   """
   
   data = {}
   
   # HJD
   t = Time('1858-11-17', format='iso') + header.get('TAI', 0.0) * u.second
   data['hjd'] = t.jd
   
   # pointing info
   data['objectname'] = header.get('SPEC_ID', '')
   data['ra'] = header.get('PLUG_RA', -1)
   data['dec'] = header.get('PLUG_DEC', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'SDSS')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['barycor'] = header.get('HELIO_RV', -1)
   data['observer'] = header.get('OBSERVER', 'UK')
   data['filetype'] = 'SDSS_final'
   
   # observing conditions
   data['wind_speed'] = header.get('WINDS', -1)
   data['wind_direction'] = header.get('WINDD', -1)
   
   data['url'] = "http://skyserver.sdss.org/dr15/en/tools/quicklook/summary.aspx?sid="+header['SPEC_ID']
   
   return data
