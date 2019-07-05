""" 
Functions to derive essential information from the header in instrument specific cases.
"""

import numpy as np
from astropy.time import Time
from observations.models import Spectrum, Observatory

import astropy.units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates.angles import Angle


def extract_header_info(header, user_info={}):
   """
   Reads the important header information and returns it as a dictionary
   """
   
   if 'ESO TEL ALT' in header:
      data = derive_eso_info(header)
   elif header.get('INSTRUME', '') == 'FEROS':
      data = derive_feros_info(header)
   elif header.get('INSTRUME', '') == 'HERMES':
      data = derive_hermes_info(header)
   elif 'SDSS' in header.get('TELESCOP', ''):
      data = derive_SDSS_info(header)
   elif 'LAMOST' in header.get('TELESCOP', ''):
      data = derive_LAMOST_info(header)
   elif 'TESS' in header.get('TELESCOP', ''):
      data = derive_TESS_info(header)
   
   else:
      data = derive_generic_info(header)
   
   #-- update the data extracted from the header with data provided by the user
   if user_info is None:
      user_info = {}
   data.update(user_info)
   
   return data
   
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
   elif 'GEOLAT' in header:
      lat, lon, alt = header.get('GEOLAT', 0), header.get('GEOLON', 0), header.get('GEOALT', 0)
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
   elif 'BJD' in header:
      data['hjd'] = header['BJD']
   elif 'MJD' in header:
      data['hjd'] = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
   else:
      data['hjd'] = 2400000
   
   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   
   try:
      data['ra'] = float(header.get('RA', None))
   except Exception:
      data['ra'] = Angle(header.get('RA', None), unit='hour').degree
   
   try:
      data['dec'] = float(header.get('DEC', None))
   except Exception:
      data['dec'] = Angle(header.get('DEC', None), unit='degree').degree
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['observer'] = header.get('OBSERVER', 'UK')
   
   data['resolution'] = header.get('SPEC_RES', -1)
   data['snr'] = header.get('SNR', -1)
   data['seeing'] = header.get('SEEING', -1)
   
   data['filetype'] = 'UK'
   
   return data

def derive_eso_info(header):
   """
   Reads header information from a standard ESO fits file
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
   
   if 'SPEC_RES' in header:
      data['resolution'] = header['SPEC_RES']
   elif 'UVES' in header.get('INSTRUME', 'UK'):
      data['resolution'] = 40000
      
   data['snr'] = header.get('SNR', -1)
   
   
   # observing conditions
   data['wind_speed'] = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   data['wind_direction'] = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   if 'ESO TEL AMBI FWHM END' in header and 'ESO TEL AMBI FWHM START' in header:
      data['seeing'] = np.average([header.get('ESO TEL AMBI FWHM END', -1), header.get('ESO TEL AMBI FWHM START', -1)])
   elif 'ESO TEL AMBI FWHM START' in header:
      data['seeing'] = header.get('ESO TEL AMBI FWHM START', -1)
   elif 'ESO TEL AMBI FWHM END' in header:
      data['seeing'] = header.get('ESO TEL AMBI FWHM END', -1)
   
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
   data['resolution'] = 48000
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
   data['resolution'] = 85000
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
   if 'TAI' in header:
      t = Time('1858-11-17', format='iso') + header.get('TAI', 0.0) * u.second
      data['hjd'] = t.jd
   elif 'MJD' in header:
      data['hjd'] = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
   else:
      data['hjd'] = 2400000
   
   # pointing info
   if 'SPEC_ID' in header:
      data['objectname'] = header.get('SPEC_ID', '')
   else:
      ra_ = "J{:02.0f}{:02.0f}{:05.2f}".format(*Angle(header.get('PLUG_RA', -1), unit='degree').hms)
      dec_ = Angle(header.get('PLUG_DEC', -1), unit='degree').dms
      data['objectname'] = ra_ + "{:+03.0f}{:02.0f}{:05.2f}".format(dec_[0], abs(dec_[1]), abs(dec_[2]))
      
   data['ra'] = header.get('PLUG_RA', -1)
   data['dec'] = header.get('PLUG_DEC', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'SDSS')
   data['telescope'] = header.get('TELESCOP', 'SDSS 2.5-M')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['resolution'] = 1900
   data['barycor'] = header.get('HELIO_RV', -1)
   data['observer'] = header.get('OBSERVER', 'UK')
   data['filetype'] = 'SDSS_final'
   
   # observing conditions
   data['wind_speed'] = header.get('WINDS', -1)
   data['wind_direction'] = header.get('WINDD', -1)
   
   if 'SPEC_ID' in header:
      data['url'] = "http://skyserver.sdss.org/dr15/en/tools/quicklook/summary.aspx?sid="+header['SPEC_ID']
   
   return data



def derive_LAMOST_info(header):
   """
   Read header information from a LAMOST spectrum
   """
   
   data = {}
   
   # HJD
   data['hjd'] = Time(header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'), format='fits').jd
   
   # pointing info
   data['objectname'] = header.get('DESIG', 'UK')
      
   data['ra'] = header.get('RA_OBS', -1)
   data['dec'] = header.get('DEC_OBS', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'LRS')
   data['telescope'] = header.get('TELESCOP', 'LAMOST')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['resolution'] = 1500
   data['barycor'] = header.get('HELIO_RV', -1)
   data['observer'] = 'UK'
   data['filetype'] = str(header.get('DATA_V', '').replace(' ', '_')) + '_' + str(header.get('ORIGIN', '')) + '_' + str(header.get('OBSID', ''))
   
   # observing conditions
   data['wind_speed'] = header.get('WINDS', -1)
   data['wind_direction'] = header.get('WINDD', -1)
   data['seeing'] = header.get('SEEING', -1)
   
   
   return data


def derive_TESS_info(header):
   """
   Read header information from a TESS lightcurve
   """
   
   data = {}
   
   # HJD
   # TESS uses truncated julian date with zero at JD=2457000
   data['hjd_start'] = 2457000 + header.get('TSTART', 0)
   data['hjd_end'] = 2457000 + header.get('TSTOP', 0)
   
   data['hjd'] = np.average([data['hjd_start'], data['hjd_end']])
   
   data['duration'] = Time(data['hjd_end']-data['hjd_start'], format='jd').jd * 24 # duration in hours
   
   # pointing info
   data['objectname'] = header.get('OBJECT', 'UK')
      
   data['ra'] = header.get('RA_OBJ', -1)
   data['dec'] = header.get('DEC_OBJ', -1)
   
   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'TESS Photometer')
   data['telescope'] = header.get('TELESCOP', 'TESS')
   data['exptime'] = 120
   data['cadence'] = 120
   data['passband'] = 'TESS.RED'
   data['observer'] = 'SPACE CRAFT'
   data['filetype'] = header.get('CREATOR', '').replace(' ', '_') + '_v_' + str(header.get('FILEVER', '')).strip() \
                      + '_rel_' + str(header.get('DATA_REL', '')).strip()
   
   return data
