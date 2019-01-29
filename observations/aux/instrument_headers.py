""" 
Functions to derive essential information from the header in instrument specific cases.
"""

import numpy as np
from astropy.time import Time
from observations.models import Spectrum, Observatory

import astropy.units as u
from astropy.coordinates import EarthLocation

def get_header_info(spectrum_pk):
   """
   Reads the important header information into the spectrum model
   """
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   wave, flux, header = spectrum.get_spectrum()
   
   if header.get('INSTRUME', '') == 'UVES':
      derive_uves_info(spectrum_pk, header)
   elif header.get('INSTRUME', '') == 'FEROS':
      derive_feros_info(spectrum_pk, header)
   elif header.get('INSTRUME', '') == 'HERMES':
      derive_hermes_info(spectrum_pk, header)
   elif 'SDSS' in header.get('TELESCOP', ''):
      derive_SDSS_info(spectrum_pk, header)
   else:
      derive_generic_info(spectrum_pk, header)

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
   

def derive_generic_info(spectrum_pk, header):
   """
   Tries to read some basic information from a unknown spectrum
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum files
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # HJD
   if 'HJD' in header:
      spectrum.hjd = header['HJD']
   if 'BJD' in header:
      spectrum.hjd = header['BJD']
   else:
      spectrum.hjd = 2400000
   
   # pointing info
   spectrum.objectname = header.get('OBJECT', '')
   spectrum.ra = header.get('RA', -1)
   spectrum.dec = header.get('DEC', -1)
   
   # telescope and instrument info
   spectrum.instrument = header.get('INSTRUME', 'UK')
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   
   spectrum.observatory = get_observatory(header, spectrum.project)
   
   
   # save changes
   spectrum.save()


def derive_uves_info(spectrum_pk, header):
   """
   Reads information from a UVES spectrum
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum files
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # HJD
   spectrum.hjd = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd
   
   # pointing info
   spectrum.objectname = header.get('OBJECT', '')
   spectrum.ra = header.get('RA', -1)
   spectrum.dec = header.get('DEC', -1)
   spectrum.alt = header.get('ESO TEL ALT', -1)
   spectrum.az = header.get('ESO TEL AZ', -1)
   spectrum.airmass = header.get('ESO TEL AIRM END', -1)
   
   # telescope and instrument info
   spectrum.instrument = header.get('INSTRUME', 'UK')
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   spectrum.barycor = header.get('ESO QC VRAD BARYCOR', -1)
   spectrum.observer = header.get('OBSERVER', 'UK')
   
   spectrum.observatory = get_observatory(header, spectrum.project)
   
   # observing conditions
   spectrum.wind_speed = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   spectrum.wind_direction = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   
   spectrum.save()


def derive_feros_info(spectrum_pk, header):
   """
   Read header information from a FEROS spectrum
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum files
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # HJD
   spectrum.hjd = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd
   
   # pointing info
   spectrum.objectname = header.get('OBJECT', '')
   spectrum.ra = header.get('RA', -1)
   spectrum.dec = header.get('DEC', -1)
   spectrum.alt = header.get('ESO TEL ALT', -1)
   spectrum.az = header.get('ESO TEL AZ', -1)
   spectrum.airmass = header.get('ESO TEL AIRM END', -1)
   
   # telescope and instrument info
   spectrum.instrument = header.get('INSTRUME', 'UK')
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   spectrum.barycor = -1
   spectrum.observer = header.get('OBSERVER', 'UK')
   
   spectrum.observatory = get_observatory(header, spectrum.project)
   
   # observing conditions
   spectrum.wind_speed = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   spectrum.wind_direction = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   
   # save changes
   spectrum.save()
   
   

def derive_hermes_info(spectrum_pk, header):
   """
   Read header information from a HERMES spectrum
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum files
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # HJD
   spectrum.hjd = header.get('BJD', 2400000)
   
   # pointing info
   spectrum.objectname = header.get('OBJECT', '')
   spectrum.ra = header.get('RA', -1)
   spectrum.dec = header.get('DEC', -1)
   spectrum.alt = header.get('TELALT', -1)
   spectrum.az = header.get('TELAZI', -1)
   spectrum.airmass = -1
   
   # telescope and instrument info
   spectrum.instrument = header.get('INSTRUME', 'UK')
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   spectrum.barycor = header.get('BVCOR', -1)
   spectrum.observer = header.get('OBSERVER', 'UK')
   
   spectrum.observatory = get_observatory(header, spectrum.project)
   
   # observing conditions
   spectrum.wind_speed = -1
   spectrum.wind_direction = -1
   
   # save changes
   spectrum.save()


def derive_SDSS_info(spectrum_pk, header):
   """
   Read header information from an SDSS spectrum
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum files
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # HJD
   spectrum.hjd = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
   
   # pointing info
   spectrum.objectname = header.get('SPEC_ID', '')
   spectrum.ra = header.get('PLUG_RA', -1)
   spectrum.dec = header.get('PLUG_DEC', -1)
   spectrum.alt = -1
   spectrum.az = -1
   spectrum.airmass = -1
   
   # telescope and instrument info
   spectrum.instrument = 'SDSS'
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   spectrum.barycor = header.get('HELIO_RV', -1)
   spectrum.observer = header.get('OBSERVER', 'UK')
   
   spectrum.observatory = get_observatory(header, spectrum.project)
   
   # observing conditions
   spectrum.wind_speed = header.get('WINDS', -1)
   spectrum.wind_direction = header.get('WINDD', -1)
   
   # save changes
   spectrum.save()
