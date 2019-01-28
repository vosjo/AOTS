import re

import numpy as np

from django.db.models import F

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, get_moon
from astroplan.moon import moon_illumination

from observations.models import Spectrum, SpecFile
from stars.models import Star

from . import instrument_headers


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


def derive_spectrum_info(spectrum_pk):
   """
   Function to derive extra information about the observations from the 
   fits files, calculate several parameters, and derive weather information
   from external sources is possible.
   
   This information is stored in the spectrum database entry
   """
   
   #-- load info from spectrum header
   instrument_headers.get_header_info(spectrum_pk)
   
   
   #-- get spectrum
   spectrum = Spectrum.objects.get(pk=spectrum_pk)
   
   #-- calculate moon parameters
   time = Time(spectrum.hjd, format='jd')
   
   # moon illumination wit astroplan (astroplan returns a fraction, but we store percentage)
   spectrum.moon_illumination =  np.round(moon_illumination(time=time)*100, 1)
   
   # get the star and moon coordinates at time and location of observations
   star = SkyCoord(ra=spectrum.ra*u.deg, dec=spectrum.dec*u.deg,)
   moon = get_moon(time)
   
   observatory = spectrum.observatory.get_EarthLocation()
   frame = AltAz(obstime=time, location=observatory)
   
   star = star.transform_to(frame)
   moon = moon.transform_to(frame)
   
   # store the separation between moon and target
   spectrum.moon_separation = np.round(star.separation(moon).degree, 1)
   
   #-- get object alt-az and airmass if not stored in header
   if spectrum.alt == 0:
      spectrum.alt = star.alt.degree
   if spectrum.az == 0:
      spectrum.az = star.az.degree
   if spectrum.airmass <= 0:
      spectrum.airmass = np.round(star.secz.value, 2)
   
   #-- save the changes
   spectrum.save()


def derive_specfile_info(specfile_id):
   """
   Read some basic info from the spectrum and store it in the database
   """
   
   specfile = SpecFile.objects.get(pk=specfile_id)
   wave, flux, h = specfile.get_spectrum()
   
   if 'MJD-OBS' in h:
      specfile.hjd = Time(h['MJD-OBS'], format='mjd', scale='utc').jd # ESO
   elif 'MJD' in h:
      specfile.hjd = Time(h['MJD'], format='mjd', scale='utc').jd # SDSS
   elif 'BJD' in h:
      specfile.hjd = h['BJD'] # HERMES
   else:
      specfile.hjd = 0
   
   specfile.instrument = h.get('INSTRUME', 'UK')
   
   if 'PIPEFILE' in h:
      specfile.filetype = h['PIPEFILE']
   elif 'INSTRUME' in h and h['INSTRUME'] == 'HERMES':
      specfile.filetype = 'MERGE_REBIN'
   elif 'SDSS' in h.get('telescop', ''):
      specfile.filetype = 'SDSS_final'
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
                   .filter(filetype__iexact = specfile.filetype) \
                   .filter(project__exact = specfile.project.pk)
                   
   if len(duplicates) > 0:
      # this specfile already exists, so remove it
      specfile.specfile.delete()
      specfile.delete()
      return False, "This specfile is a duplicate and was not added!"
   
   
   #-- add specfile to existing or new spectrum
   spectrum = Spectrum.objects.filter(instrument__iexact = specfile.instrument, project__exact=specfile.project) \
                              .filter(hjd__range = (specfile.hjd - 0.001, specfile.hjd + 0.001))
   
   if len(spectrum) > 0:
      spectrum = spectrum[0]
      spectrum.specfile_set.add(specfile)
      message += "Specfile added to existing Spectrum {}".format(spectrum)
   else:
      spectrum = Spectrum(project=specfile.project)
      spectrum.save()
      spectrum.specfile_set.add(specfile)
   
      #-- load extra information for the spectrum
      derive_spectrum_info(spectrum.id)
      spectrum.refresh_from_db() # spectrum is not updated automaticaly!
      message += "Specfile added to new Spectrum {}".format(spectrum)
   
   
   #-- add the spectrum to existing or new star
   star = Star.objects.filter(project__exact=spectrum.project) \
                       .filter(ra__range = (spectrum.ra - 0.1, spectrum.ra + 0.1)) \
                       .filter(dec__range = (spectrum.dec - 0.1, spectrum.dec + 0.1))
   
   if len(star) > 0:
      # there is one or more stars returned, select the closest star
      star = star.annotate(distance=((F('ra')-spectrum.ra)**2 + (F('dec')-spectrum.dec)**2)**(1./2.)).order_by('distance')[0]
      star.spectrum_set.add(spectrum)
      message += ", and added to existing System {} (_r = {})".format(star, star.distance)
      return True, message
   else:
      # need to make a new star
      w, f, header = specfile.get_spectrum()
      
      star = Star(name= header.get('OBJECT', ''), ra=spectrum.ra, dec=spectrum.dec, project=spectrum.project)
      star.save()
      
      star = Star.objects.get(pk=star.pk)
      star.spectrum_set.add(spectrum)
      
      message += ", and added to new System {}".format(star)
      return True, message
