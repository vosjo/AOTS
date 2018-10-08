import re
import ephem

import numpy as np

from astropy.time import Time
from spectra.models import Spectrum, SpecFile
from stars.models import Star
from stars.aux import add_star_from_spectrum

from . import instrument_headers
from . import observatories

from django.contrib import messages

def get_wind_direction(degrees):
   """
   Converts degrees to a direction
   """
   if degrees < 0 or degrees > 360:
      return 'NA'
   if degrees > 337.5 or degrees < 22.5:
      return 'N'
   elif degrees < 67.5:
      return 'NE'
   elif degrees < 112.5:
      return 'E'
   elif degrees < 157.5:
      return 'SE'
   elif degrees < 202.5:
      return 'S'
   elif degrees < 247.5:
      return 'SW'
   elif degrees < 292.5:
      return 'W'
   else:
      return 'NW'

def get_seeing_paranal(date):
   """
   queries the paranal historical ambient conditions to get seeing at given date
   
   Weather links:
   http://archive.eso.org/cms/eso-data/ambient-conditions/paranal-ambient-query-forms.html
   http://archive.eso.org/wdb/wdb/asm/dimm_paranal/form
   http://archive.eso.org/wdb/wdb/asm/meteo_paranal/form
   http://archive.eso.org/wdb/wdb/asm/historical_ambient_paranal/form
   
   http://archive.eso.org/asm/ambient-server?night=14+oct+2011&site=paranal
   """
   
   return 0

def derive_spectrum_info(spectrum_pk):
   """
   Function to derive extra information about the observations from the 
   fits files, calculate several parameters, and derive weather information
   from external sources is possible.
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum header
   instrument_headers.get_header_info(spectrum_pk)
   
   
   #-- calculate moon parameters with ephem
   
   # get spectrum
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   # the observatory
   observatory = observatories.get_observatory(spectrum.telescope)
   observatory.date = Time(spectrum.hjd, format='jd').iso
   moon = ephem.Moon()
   
   # the star
   star = ephem.FixedBody()
   star._ra = ephem.degrees(spectrum.ra/180.*np.pi)
   star._dec = ephem.degrees(spectrum.dec/180*np.pi)
   
   # the actual calculation
   star.compute(observatory)
   moon.compute(observatory)
   spectrum.moon_illumination =  np.round(moon.phase, 1)
   spectrum.moon_separation = str(ephem.separation(moon,star)).split(':')[0]
   
   #-- save the changes
   spectrum.save()

def derive_specfile_info(specfile_id):
   """
   Read some basic info from the spectrum and store it in the database
   """
   
   specfile = SpecFile.objects.get(pk=specfile_id)
   wave, flux, h = specfile.get_spectrum()
   
   if 'MJD-OBS' in h:
      specfile.hjd = Time(h['MJD-OBS'], format='mjd', scale='utc').jd
   elif 'BJD' in h:
      specfile.hjd = h['BJD'] # HERMES
   else:
      specfile.hjd = 0
   
   specfile.instrument = h.get('INSTRUME', 'UK')
   
   if 'PIPEFILE' in h:
      specfile.filetype = h['PIPEFILE']
   elif 'INSTRUME' in h and h['INSTRUME'] == 'HERMES':
      specfile.filetype = 'MERGE_REBIN'
   else:
      specfile.filetype = 'UK'
   
   specfile.save()
   
def process_specfile(specfile_id):
   """
   Check if the specfile is a duplicate, and if not, add it to a spectrum
   and target star.
   
   returns success, message
   success is True is the specfile was successfully added, False otherwise. 
   the message contains info on what went wrong, or just a success message
   """
   
   message = ""
   
   derive_specfile_info(specfile_id)
   
   specfile = SpecFile.objects.get(pk=specfile_id)
   
   #-- check for duplicates
   duplicates = SpecFile.objects.exclude(id__exact = specfile_id) \
                   .filter(hjd__exact = specfile.hjd) \
                   .filter(instrument__iexact = specfile.instrument) \
                   .filter(filetype__iexact = specfile.filetype)
                   
   if len(duplicates) > 0:
      # this specfile already exists, so remove it
      specfile.specfile.delete()
      specfile.delete()
      return False, "This specfile is a duplicate and was not added!"
   
   
   #-- add specfile to existing or new spectrum
   spectrum = Spectrum.objects.filter(instrument__iexact = specfile.instrument) \
                              .filter(hjd__range = (specfile.hjd - 0.001, specfile.hjd + 0.001))
   
   if len(spectrum) > 0:
      spectrum = spectrum[0]
      spectrum.specfile_set.add(specfile)
      message += "Specfile added to existing Spectrum {}".format(spectrum)
   else:
      spectrum = Spectrum()
      spectrum.save()
      spectrum.specfile_set.add(specfile)
   
      #-- load extra information for the spectrum
      derive_spectrum_info(spectrum.id)
      spectrum.refresh_from_db() # spectrum is not updated automaticaly!
      message += "Specfile added to new Spectrum {}".format(spectrum)
   
   
   #-- add the spectrum to existing or new star
   star = Star.objects.filter(ra__range = (spectrum.ra - 0.1, spectrum.ra + 0.1)) \
                       .filter(dec__range = (spectrum.dec - 0.01, spectrum.dec + 0.01))
   
   if len(star) > 0:
      # there is an existing star
      star = star[0]
      star.spectrum_set.add(spectrum)
      message += ", and added to existing System {}".format(star)
      return True, message
   else:
      # need to make a new star
      w, f, header = specfile.get_spectrum()
      star_id = add_star_from_spectrum(header)
      
      star = Star.objects.get(pk=star_id)
      star.spectrum_set.add(spectrum)
      
      message += ", and added to new System {}".format(star)
      return True, message
