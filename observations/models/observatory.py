
import astropy.units as u
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from stars.models import Project


def validate_weatherurl_template(value):
    """Allow http(s) URLs or http(s) format templates; reject javascript:/data:."""
    if not value:
        return
    raw = value.strip()
    lower = raw.lower()
    if lower.startswith(('javascript:', 'data:', 'vbscript:')):
        raise ValidationError('Only http and https weather URLs are allowed.')
    if '{' not in raw:
        URLValidator(schemes=['http', 'https'])(raw)
        return
    if not (lower.startswith('http://') or lower.startswith('https://')):
        raise ValidationError('Weather URL template must start with http:// or https://.')


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

    weatherurl = models.CharField(
        max_length=150,
        default='',
        blank=True,
        validators=[validate_weatherurl_template],
    )

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
      is used. Only http(s) templates are returned.
      """
        if hjd is None:
            hjd = Time.now()

        if self.weatherurl != '':
            raw = self.weatherurl.strip()
            # Reject javascript:/data: etc. even if legacy rows bypassed the validator.
            lower = raw.lower()
            if not (lower.startswith('http://') or lower.startswith('https://') or '{year}' in raw):
                # Allow format templates that expand to http(s)
                if 'javascript:' in lower or 'data:' in lower:
                    return ''
            t = Time(hjd, format='jd')
            dt = t.datetime
            url = self.weatherurl.format(
                year=dt.year, month=dt.month, day=dt.day,
                hour=dt.hour, min=dt.minute, sec=dt.second,
                mjd=t.mjd, hjd=t.jd,
            )
            if not (url.lower().startswith('http://') or url.lower().startswith('https://')):
                return ''
            return url
        else:
            return ''

    # -- representation of self
    def __str__(self):
        return f"{self.name}: lat={self.latitude}, lon={self.longitude}, alt={self.altitude}"


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
                if len(word) > 3:
                    short_name += word[0].upper()

        # print ('shortname: ', short_name)
        observatory.short_name = short_name
