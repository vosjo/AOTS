from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from stars.models import Star

band_wavelengths = {'GALEX.FUV':  1535, 
                    'GALEX.NUV':  2300, 
                    'APASS.B':    4303,
                    'APASS.V':    5437,
                    '2MASS.J':    12393,
                    '2MASS.H':    16494,
                    '2MASS.K':    21638,}  
                 
      

@python_2_unicode_compatible  # to support Python 2
class Photometry(models.Model):
   """
   A photometric measurement. We only save the observed value, 
   values in other units like fluxes have to be calculated.
   There is no wavelength saved, only the bandname. Wavelength 
   would then be redundant.
   """
   
   class Meta():
      ordering = ['wavelength', 'band']
   
   #-- a photometry measurement belongs to one star only
   star = models.ForeignKey(Star, on_delete=models.CASCADE)
   
   band = models.CharField(max_length=50)
   wavelength = models.FloatField(default=0)
   
   #-- measurement can be in any unit
   measurement = models.FloatField()
   error = models.FloatField()
   unit = models.CharField(max_length=50)
   
   #-- source to keep an article reference or reference to a vizier table
   source = models.TextField(default='')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   #-- representation of self
   def __str__(self):
      return "{} = {} +- {} {}".format(self.band, self.measurement, self.error, self.unit)
   
   def save(self, *args, **kwargs):
      if self.band in band_wavelengths:
         self.wavelength = band_wavelengths[self.band]
      
      super(Photometry, self).save(*args, **kwargs)