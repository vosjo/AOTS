from __future__ import unicode_literals

import astropy.units as u
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
from six import python_2_unicode_compatible

from stars.models import Project
from users.models import get_sentinel_user


@python_2_unicode_compatible  # to support Python 2
class Observatory(models.Model):
    # -- an observatory belongs to a specific project
    #   when that project is deleted, the observatory is also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    name = models.CharField(max_length=100, default='')

    short_name = models.CharField(max_length=15, default='', blank=True)

    telescopes = models.TextField(default='', blank=True)

    # latitude in degrees
    latitude = models.FloatField(default=0)

    # longitude in degrees
    longitude = models.FloatField(default=0)

    # altitude in meter
    altitude = models.FloatField(default=0)

    # if observatory is a space craft no coordinates are necessary
    space_craft = models.BooleanField(default=False)

    url = models.CharField(max_length=150, default='', blank=True)

    weatherurl = models.CharField(max_length=150, default='', blank=True)

    note = models.TextField(default='', blank=True)

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    def get_EarthLocation(self):
        """
      Returns the astropy earthlocation of this observatory
      """
        return EarthLocation(lat=self.latitude * u.deg, lon=self.longitude * u.deg, height=self.altitude * u.m)

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
            print(hjd)
            t = Time(hjd, format='jd')
            dt = t.datetime
            return self.weatherurl.format(year=dt.year, month=dt.month, day=dt.day,
                                          hour=dt.hour, min=dt.minute, sec=dt.second,
                                          mjd=t.mjd, hjd=t.jd)
        else:
            return ''

    # -- representation of self
    def __str__(self):
        return "{}: lat={}, lon={}, alt={}".format(self.name, self.latitude, self.longitude, self.altitude)


@receiver(pre_save, sender=Observatory)
def set_short_name(sender, **kwargs):
    """
   When an observatory is saved, create a short name is none was set.
   """

    if kwargs.get('raw', False):
        return

    observatory = kwargs['instance']

    # print (observatory)

    if observatory.short_name == '':
        # create short name
        short_name = ''
        if len(observatory.name) <= 15:
            # if name is less than 15 chars, just use the name
            short_name = observatory.name

        else:
            # take the first letter of each word longer than 3 chars.
            for word in observatory.name.split():
                if len(word) > 3: short_name += word[0].upper()

        # print ('shortname: ', short_name)
        observatory.short_name = short_name
