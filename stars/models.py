#from __future__ import unicode_literals

from astropy.coordinates.angles import Angle

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

# Create your models here.

@python_2_unicode_compatible  # to support Python 2
class Tag(models.Model):
   """
   A tag that can be added to a star to facilitate grouping
   """
   #-- Multiple stars can have the same tag, and multiple tags can be added to one star
   
   name = models.CharField(max_length=75)
   
   description = models.TextField(default='')
   
   color = models.CharField(max_length=7, default='#8B0000') # color as hex color value
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   #-- representation of self
   def __str__(self):
      return "{}:{}".format(self.name, self.description)

@python_2_unicode_compatible  # to support Python 2
class Star(models.Model):
   name = models.CharField(max_length=200)
   
   #-- coordinates in decimal form
   ra = models.FloatField()
   dec = models.FloatField()
   
   #-- spectral classification
   classification = models.CharField(max_length=50)
   
   SPECTROSCOPIC = 'SP'
   PHOTOMETRIC = 'PH'
   CLASSIFICATION_TYPE_CHOICES = (
      (SPECTROSCOPIC, 'Spectroscopic'),
      (PHOTOMETRIC,  'Photometric'),)
   
   classification_type = models.CharField(
      max_length=2,
      choices=CLASSIFICATION_TYPE_CHOICES,
      default= PHOTOMETRIC               )
   
   #-- observing
   FINISHED = 'FI'
   ONGOING = 'ON'
   REJECTED = 'RE'
   NEW = 'NE'
   OBSERVING_STATUS_CHOICES = (
      (FINISHED, 'Finished'),
      (ONGOING,  'Ongoing'),
      (REJECTED, 'Rejected'),
      (NEW,      'New')       )
   observing_status = models.CharField(
      max_length=2,
      choices=OBSERVING_STATUS_CHOICES,
      default=NEW                     )
   
   
   note = models.TextField(default='')
   
   #-- tags
   tags = models.ManyToManyField(Tag, related_name='stars')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   def get_system_summary_parameter(self):
      """
      Returns a list of parameters that should be included in the 
      summary part of the star. 
      """
      pars = []
      
      for name in ['p', 't0', 'e']:
         p = self.parameter_set.filter(name__exact=name, average__exact=True)
         if len(p) > 0:
            p = p[0]
            pars.append( (name, p.unit, "{} &pm; {}".format(p.rvalue(), p.rerror())) )
      
      return pars
   
   def get_component_summary_parameter(self):
      """
      Returns a list of parameters that should be included in the 
      summary part of the star. 
      """
      pars = []
      
      for name in ['teff', 'logg', 'rad']:
         p1 = self.parameter_set.filter(name__exact=name, component__exact = 1,
                                        average__exact=True)
         p2 = self.parameter_set.filter(name__exact=name, component__exact = 2,
                                        average__exact=True)

         v1 = "{} &pm; {}".format(p1[0].rvalue(), p1[0].rerror()) if len(p1) > 0 else "/"
         v2 = "{} &pm; {}".format(p2[0].rvalue(), p2[0].rerror()) if len(p2) > 0 else "/"
         
         if len(p1) > 0 or len(p2) > 0:
            unit = p1[0].unit if len(p1) > 0 else p2[0].unit
            pars.append( (name, unit, v1, v2) )
      
      return pars
   
   #-- hms and dms representation for ra and dec
   def ra_hms(self):
      try:
         a = Angle(float(self.ra), unit='degree').hms
      except Exception, e:
         return self.ra
      return "{:02.0f}:{:02.0f}:{:05.2f}".format(*a)
   
   def dec_dms(self):
      try:
         a = Angle(float(self.dec), unit='degree').dms
      except Exception, e:
         return self.dec
      return "{:+03.0f}:{:02.0f}:{:05.2f}".format(a[0], abs(a[1]), abs(a[2]))
   
   #-- representation of self
   def __str__(self):
      return "{}: {} {}".format(self.name, self.ra, self.dec)


@python_2_unicode_compatible  # to support Python 2
class Identifier(models.Model):
   """
   An alternative name for a star
   """
   #-- Altnames should be removed when the star is removed
   star = models.ForeignKey(Star, on_delete=models.CASCADE)
   
   name = models.CharField(max_length=200)
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   #-- representation of self
   def __str__(self):
      return "{} = {}".format(self.star.name, self.name)


#@python_2_unicode_compatible  # to support Python 2
#class Photometry(models.Model):
   #"""
   #A photometric measurement. We only save the observed value, 
   #values in other units like fluxes have to be calculated.
   #There is no wavelength saved, only the bandname. Wavelength 
   #would then be redundant.
   #"""
   
   ##-- a photometry measurement belongs to one star only
   #star = models.ForeignKey(Star, on_delete=models.CASCADE)
   
   #band = models.CharField(max_length=50)
   
   ##-- measurement can be in any unit
   #measurement = models.FloatField()
   #error = models.FloatField()
   #unit = models.CharField(max_length=50)
   
   ##-- bookkeeping
   #added_on = models.DateTimeField(auto_now_add=True)
   #last_modified = models.DateTimeField(auto_now=True)
   
   ##-- representation of self
   #def __str__(self):
      #return "{} = {} +- {} {}".format(self.band, self.measurement, self.error, self.unit)