""" 
Functions to derive essential information from the header in instrument specific cases.
"""

import numpy as np
from astropy.time import Time
from spectra.models import Spectrum

def get_header_info(spectrum_pk):
   """
   Reads the important header information into the spectrum model
   """
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   wave, flux, header = spectrum.get_spectrum()
   
   if header['INSTRUME'] == 'UVES':
      derive_uves_info(spectrum_pk, header)
   elif header['INSTRUME'] == 'FEROS':
      derive_feros_info(spectrum_pk, header)
   elif header['INSTRUME'] == 'HERMES':
      derive_hermes_info(spectrum_pk, header)
   else:
      derive_generic_info(spectrum_pk, header)


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
   spectrum.ra = header.get('RA', -1)
   spectrum.dec = header.get('DEC', -1)
   
   # telescope and instrument info
   spectrum.instrument = header.get('INSTRUME', 'UK')
   spectrum.telescope = header.get('TELESCOP', 'UK')
   spectrum.exptime = np.round(header.get('EXPTIME', -1), 0)
   
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
   
   # observing conditions
   spectrum.wind_speed = -1
   spectrum.wind_direction = -1
   
   # save changes
   spectrum.save()

