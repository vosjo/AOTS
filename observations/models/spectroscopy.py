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
from astropy.io import fits

# Create your models here.

@python_2_unicode_compatible  # to support Python 2
class Spectrum(models.Model):
   
   #-- a spectrum belongs to one star only and is deleted when the star 
   #   is deleted. However, a star can be added after creation.
   star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- a spectrum belongs to a specific project
   #   when that project is deleted, the spectrum is also deleted.
   project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False,)
   
   hjd = models.FloatField(default=0)
   
   #-- pointing info
   objectname = models.CharField(max_length=50, default='')
   ra = models.FloatField(default=0)
   dec = models.FloatField(default=0)
   alt = models.FloatField(default=0)  # average altitude angle of observation
   az = models.FloatField(default=0)   # average azimut angle of observation
   airmass = models.FloatField(default=0) # average airmass
   
   #-- telescope and instrument info
   exptime = models.FloatField(default=0) # s
   barycor = models.FloatField(default=0) # km/s
   telescope = models.CharField(max_length=200, default='')
   instrument = models.CharField(max_length=200, default='')
   observer = models.CharField(max_length=50, default='')
   
   #-- observing conditions
   moon_illumination = models.FloatField(default=0) # percent of illumination of the moon
   moon_separation = models.FloatField(default=0) # angle between target and moon
   wind_speed = models.FloatField(default=0) # in m/s
   wind_direction = models.FloatField(default=0) # in degrees
   seeing = models.FloatField(default=0) # in mas
   
   #-- observatory
   #   prevent deletion of an observatory that is referenced by a spectrum
   observatory = models.ForeignKey(Observatory, on_delete=models.PROTECT, null=True,)
   
   #-- flag if the spectrum is flux calibrated, defaults to False. And the flux unit.
   fluxcal = models.BooleanField(default=False)
   flux_units = models.CharField(max_length=50, default='ergs/cm/cm/s/A')
   
   #-- flag to indicate that the spectrum is of good quality
   valid = models.BooleanField(default=True)
   
   note = models.TextField(default='', blank=True)
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), null=True)
   
   #-- function to get the spectrum
   def get_spectrum(self):
      files = self.specfile_set.all()
      if len(files) == 0:
         return None, None, None
      else:
         return files[0].get_spectrum()
   
   def get_weather_url(self):
      if not self.observatory is None:
         return self.observatory.get_weather_url(hjd=self.hjd)
      else:
         return ''
   
   #-- representation of self
   def __str__(self):
      return "{}@{} - {}".format(self.instrument, self.telescope, self.hjd)


@python_2_unicode_compatible  # to support Python 2
class SpecFile(models.Model):
   """
   Model to represent an uploaded spectrum file. Can be fits or hdf5.
   A spectrum can exists out of different files (fx. BLUE, REDL and REDU for uves).
   
   This setup allows us to keep links to the uploaded files in the database even 
   when the spectra are deleted. The spectra, and even targets can be rebuild 
   from the information in the specfiles.
   """
   
   #-- a specfile belongs to a spectrum but does not need to be deleted when the
   #   spectrum is deleted, as the spectrum can be rebuild from the info in the
   #   specfile.
   spectrum = models.ForeignKey(Spectrum, on_delete=models.SET_NULL, blank=True, null=True,)
   
   #-- a specfile belongs to a specific project
   #   when that project is deleted, the star is also deleted.
   project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False,)
   
   #-- fields necesary to detect doubles. If spectra have same hjd, instrument and file
   #   type, they are probably the same spectrum
   hjd = models.FloatField(default=0)
   instrument = models.CharField(max_length=200, default='')
   filetype = models.CharField(max_length=200, default='')
   
   specfile = models.FileField(upload_to='spectra/')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), null=True)
   
   def get_spectrum(self):
      return fileio.read_spectrum(self.specfile.path, return_header=True)
   
   def get_header(self, hdu=0):
      try:
         header = fits.getheader(self.specfile.path, hdu)
         h = {}
         for k, v in header.items():
            if k != 'comment' and k != 'history' and k != '':
               h[k] = v
      except Exception as e:
         print (e)
         h = {}
      return h
   
   #-- representation of self
   def __str__(self):
      return "{}@{} - {}".format(self.hjd, self.instrument, self.filetype)


# Handler to assure the deletion of a specfile removes the actual file, and if necessary the 
# spectrum that belongs to this file
@receiver(post_delete, sender=SpecFile)
def specFile_post_delete_handler(sender, **kwargs):
    specfile = kwargs['instance']
    # check if the spectrum has any specfiles left, otherwise delete it
    if not specfile.spectrum is None and not specfile.spectrum.specfile_set.exists():
       specfile.spectrum.delete()
    
    # delete the actual specfile
    try:
      storage, path = specfile.specfile.storage, specfile.specfile.path
      storage.delete(path)
    except Exception as e:
       print (e)
