from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from django.conf import settings

from django.utils.encoding import python_2_unicode_compatible

from stars.models import Star, Project
from users.models import get_sentinel_user
from .observatory import Observatory

from observations.aux import fileio 


@python_2_unicode_compatible  # to support Python 2
class LightCurve(models.Model):
   
   #-- a spectrum belongs to one star only and is deleted when the star 
   #   is deleted. However, a star can be added after creation.
   star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- a spectrum belongs to a specific project
   #   when that project is deleted, the spectrum is also deleted.
   project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False,)
   
   hjd = models.FloatField(default=0)
   
   hjd_start = models.FloatField(default=0)
   hjd_end = models.FloatField(default=0)
   
   #-- pointing info
   objectname = models.CharField(max_length=50, default='')
   ra = models.FloatField(default=0)
   dec = models.FloatField(default=0)
   alt = models.FloatField(default=0)  # average altitude angle of observation
   az = models.FloatField(default=0)   # average azimut angle of observation
   airmass = models.FloatField(default=0) # average airmass
   
   #-- telescope and instrument info
   exptime = models.FloatField(default=0) # s
   cadence = models.FloatField(default=0) # s
   telescope = models.CharField(max_length=200, default='')
   instrument = models.CharField(max_length=200, default='')
   observer = models.CharField(max_length=50, default='')
   
   #-- observing conditions
   moon_illumination = models.FloatField(default=0) # percent of illumination of the moon
   moon_separation = models.FloatField(default=0) # angle between target and moon
   wind_speed = models.FloatField(default=-1) # in m/s
   wind_direction = models.FloatField(default=-1) # in degrees
   seeing = models.FloatField(default=0) # in mas
   
   #-- observatory
   #   prevent deletion of an observatory that is referenced by a spectrum
   observatory = models.ForeignKey(Observatory, on_delete=models.PROTECT, null=True,)
   
   
   #-- flag to indicate that the lc is of good quality
   valid = models.BooleanField(default=True)
   
   note = models.TextField(default='', blank=True)
   
   lcfile = models.FileField(upload_to='lightcurves/')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), null=True)
   
   #-- function to get the spectrum
   def get_lightcurve(self):
      return fileio.read_lightcurve(self.lcfile.path, return_header=True)
   
   def get_weather_url(self):
      if not self.observatory is None:
         return self.observatory.get_weather_url(hjd=self.hjd)
      else:
         return ''
   
   #-- representation of self
   def __str__(self):
      return "{}@{} - {}".format(self.instrument, self.telescope, self.hjd)
   
   
# Handler to assure the deletion of a specfile removes the actual file, and if necessary the 
# spectrum that belongs to this file
@receiver(post_delete, sender=LightCurve)
def specFile_post_delete_handler(sender, **kwargs):
    lc = kwargs['instance']
        
    # delete the actual specfile
    try:
      storage, path = lc.lcfile.storage, lc.lcfile.path
      storage.delete(path)
    except Exception as e:
       print (e)
