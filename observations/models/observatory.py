 
from __future__ import unicode_literals

from django.db import models

from django.conf import settings

from django.utils.encoding import python_2_unicode_compatible

from stars.models import Project
from users.models import get_sentinel_user

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation
from astroplan import Observer

@python_2_unicode_compatible  # to support Python 2
class Observatory(models.Model):
   
   #-- an observatory belongs to a specific project
   #   when that project is deleted, the observatory is also deleted.
   project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False,)
   
   name = models.CharField(max_length=100, default='')
   
   telescopes = models.TextField(default='')
   
   # latitude in degrees
   latitude = models.FloatField(default=0)
   
   # longitude in degrees
   longitude = models.FloatField(default=0)
   
   # altitude in meter
   altitude = models.FloatField(default=0)
   
   
   url = models.CharField(max_length=150, default='')
   
   weatherurl = models.CharField(max_length=150, default='')
   
   note = models.TextField(default='')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), null=True)
   
   
   def get_EarthLocation(self):
      """
      Returns the astropy earthlocation of this observatory
      """
      return EarthLocation(lat=self.latitude*u.deg, lon=self.longitude*u.deg, height=self.altitude*u.m)
      
   def get_sunset_sunrise(self, time):
      """
      Returns the sunset and sunrise times of the night containing the time provided
      time is a astropy Time object
      The sunset and sunrise times are returns as an astropy Time object with the same 
      settings as the provided Time object. 
      """
      observer = Observer(location=self.get_EarthLocation())
      sunset = observer.sun_set_time(time, which='nearest')
      sunrise = observer.sun_rise_time(time, which='nearest')
      
      return sunset, sunrise
   
   def get_weather_url(self, hjd=None):
      """
      Returns the weather url set to the given time (hjd). If no time is given, the current time
      is used.
      """
      if hjd is None:
         hjd = Time.now()
      
      if self.weatherurl != '':
         print (hjd)
         t = Time(hjd, format='jd')
         dt = t.datetime
         return self.weatherurl.format(year=dt.year, month=dt.month, day=dt.day, 
                                       hour=dt.hour, min=dt.minute, sec=dt.second,
                                       mjd=t.mjd, hjd=t.jd)
      else:
         return ''
   
   #-- representation of self
   def __str__(self):
      return "{}: lat={}, lon={}, alt={}".format(self.name, self.latitude, self.longitude, self.altitude)
