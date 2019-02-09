import re

import numpy as np

from django.db.models import F

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, get_moon
from astroplan.moon import moon_illumination

from observations.models import LightCurve
from stars.models import Star

from . import instrument_headers

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def derive_lightcurve_info(lightcurve_pk):
   """
   Function to derive extra information about the observations from the 
   fits files, calculate several parameters, and derive weather information
   from external sources is possible.
   
   This information is stored in the lightcurve database entry
   """
   
   #-- get lightcurve
   lightcurve = LightCurve.objects.get(pk=lightcurve_pk)
   hjd, flux, header = lightcurve.get_lightcurve()
   
   
   #-- load info from lightcurve header
   data = instrument_headers.extract_header_info(header)
   
   # HJD
   lightcurve.hjd = data.get('hjd', 2400000)
   lightcurve.hjd_start = data.get('hjd_start', 2400000)
   lightcurve.hjd_end = data.get('hjd_end', 2400000)
   
   # pointing info
   lightcurve.objectname = data.get('objectname', '')
   lightcurve.ra = data.get('ra', -1)
   lightcurve.dec = data.get('dec', -1)
   lightcurve.alt = data.get('alt', -1)
   lightcurve.az = data.get('az', -1)
   lightcurve.airmass = data.get('airmass', -1)
   
   # telescope and instrument info
   lightcurve.instrument = data.get('instrument', 'UK')
   lightcurve.telescope = data.get('telescope', 'UK')
   lightcurve.passband = data.get('passband', 'UK')
   lightcurve.exptime = data.get('exptime', -1)
   lightcurve.cadence = data.get('cadence', -1)
   lightcurve.duration = data.get('duration', -1)
   lightcurve.observer = data.get('observer', 'UK')
   lightcurve.filetype = data.get('filetype', 'UK')
   
   # observing conditions
   if isfloat(data.get('wind_speed', -1)):
      lightcurve.wind_speed = data.get('wind_speed', -1)
   
   if isfloat(data.get('wind_direction', -1)):
      lightcurve.wind_direction = data.get('wind_direction', -1)
      
   lightcurve.seeing = data.get('seeing', -1)

   
   
   #-- observatory
   lightcurve.observatory = instrument_headers.get_observatory(header, lightcurve.project)
   
   #-- save the changes
   lightcurve.save()
   
   #-- if the observatory is in space, no moon ect can be calculated
   if lightcurve.observatory.space_craft:
      return
   
   #-- calculate moon parameters
   time = Time(lightcurve.hjd, format='jd')
   
   # moon illumination wit astroplan (astroplan returns a fraction, but we store percentage)
   lightcurve.moon_illumination =  np.round(moon_illumination(time=time)*100, 1)
   
   # get the star and moon coordinates at time and location of observations
   star = SkyCoord(ra=lightcurve.ra*u.deg, dec=lightcurve.dec*u.deg,)
   moon = get_moon(time)
   
   observatory = lightcurve.observatory.get_EarthLocation()
   frame = AltAz(obstime=time, location=observatory)
   
   star = star.transform_to(frame)
   moon = moon.transform_to(frame)
   
   # store the separation between moon and target
   lightcurve.moon_separation = np.round(star.separation(moon).degree, 1)
   
   #-- get object alt-az and airmass if not stored in header
   if lightcurve.alt == 0:
      lightcurve.alt = star.alt.degree
   if lightcurve.az == 0:
      lightcurve.az = star.az.degree
   if lightcurve.airmass <= 0:
      lightcurve.airmass = np.round(star.secz.value, 2)
   
   #-- save the changes
   lightcurve.save()

   

def process_lightcurve(lightcurve_id, create_new_star=True):
   """
   Check if the specfile is a duplicate, and if not, add it to a spectrum
   and target star.
   
   returns success, message
   success is True is the specfile was successfully added, False otherwise. 
   the message contains info on what went wrong, or just a success message
   """
   
   message = ""
   
   derive_lightcurve_info(lightcurve_id)
   
   lightcurve = LightCurve.objects.get(pk=lightcurve_id)
   
   #-- check for duplicates
   duplicates = LightCurve.objects.exclude(id__exact = lightcurve_id) \
                   .filter(ra__range = [lightcurve.ra-1/3600., lightcurve.ra+1/3600.]) \
                   .filter(dec__range = [lightcurve.dec-1/3600., lightcurve.dec+1/3600.]) \
                   .filter(hjd__exact = lightcurve.hjd) \
                   .filter(instrument__iexact = lightcurve.instrument) \
                   .filter(project__exact = lightcurve.project.pk)
                   
   if len(duplicates) > 0:
      # this specfile already exists, so remove it
      lightcurve.lcfile.delete()
      lightcurve.delete()
      return False, "This light curve is a duplicate and was not added!"
   
   
   message += "New light curve"
   
   #-- add the lightcurve to existing or new star if the spectrum is newly created
   star = Star.objects.filter(project__exact=lightcurve.project) \
                       .filter(ra__range = (lightcurve.ra - 0.1, lightcurve.ra + 0.1)) \
                       .filter(dec__range = (lightcurve.dec - 0.1, lightcurve.dec + 0.1))
   
   if len(star) > 0:
      # there is one or more stars returned, select the closest star
      star = star.annotate(distance=((F('ra')-lightcurve.ra)**2 + (F('dec')-lightcurve.dec)**2)**(1./2.)).order_by('distance')[0]
      star.lightcurve_set.add(lightcurve)
      message += ", added to existing System {} (_r = {})".format(star, star.distance)
      return True, message
   else:
      
      if not create_new_star:
         lightcurve.lcfile.delete()
         lightcurve.delete()
         message += ", no star found, light curve NOT added to database."
         return False, message
      
      # need to make a new star
      star = Star(name= lightcurve.objectname, ra=lightcurve.ra, dec=lightcurve.dec, project=lightcurve.project)
      star.save()
      
      star.lightcurve_set.add(lightcurve)
      
      message += ", added to new System {}".format(star)
      return True, message
