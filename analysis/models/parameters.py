#from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from stars.models import Star
from .datasource import  DataSet, DataTable, DataSource

import numpy as np


#-- PARAMETER related constants

SYSTEM = 0
PRIMARY = 1
SECONDARY = 2
CBDISK = 5
COMPONENT_CHOICES = (
   (SYSTEM, 'System'),
   (PRIMARY,  'Primary'),
   (SECONDARY, 'Secondary'),      
   (CBDISK, 'Circumbinary Disk'),)

#SYSTEM_PARAMETERS = ['p', 't0', 'e', 'omega', 'ebv']
STELLAR_PARAMETERS = [PRIMARY, SECONDARY]

#-- PARAMETER rounding
PARAMETER_DECIMALS = {
   'teff':0, 
   'logg':2, 
   'rad':2, 
   'ebv':3,
   'z':2,
   'met':2,
   'vmicro': 1,
   'vrot':0,
   'dilution':2,
   'p':0, 
   't0':0, 
   'e':3, 
   'omega':2, 
   'K':2, 
   'v0':2,
   }

def round_value(value, name):
   """
   Rounds a value based on the parameter name
   """
   if name[-1] == '1' or name[-1] == '2':
      name = name[:-1]
   
   decimals = PARAMETER_DECIMALS.get(name, 3)
   if decimals > 0:
      return np.round(value, decimals)
   else:
      return int(value)

#-- PARAMETER sorting
PARAMETER_ORDER = {
   'p':     00, 
   't0':    01, 
   'e':     02, 
   'omega': 03, 
   'K':     04, 
   'v0':    05,
   
   'teff':    10, 
   'logg':    11, 
   'rad':     12, 
   'ebv':     13,
   'z':       14,
   'met':     14,
   'vmicro':  15,
   'vrot':    16,
   'dilution':17,
   }

def parameter_order(name):
   """
   returns the parameter order based on its name
   """
   if name in PARAMETER_ORDER:
      return PARAMETER_ORDER[name]
   else:
      return 20



class ParameterManager(models.Manager):
   """
   Custom manager for Parameter class to provide sorting of the parameters in a more
   sensible fasion then alphabetical (provides standard order options)
   """
   def order_by(self, *args, **kwargs):
      super(ParameterManager, self).get_query_set().order_by(*args, **kwargs)
       
   def order(self, *args, **kwargs):
      parameters = self.get_queryset().all()
      sorted_results = sorted(parameters, key= lambda t: t.order())
      return sorted_results
   
   
@python_2_unicode_compatible  # to support Python 2
class Parameter(models.Model):
   """
   A simple parameter belonging to a parameter set
   The parameter consists of a value, error and unit
   """
   
   #-- provide custom sorting options that make sense
   objects = ParameterManager()
   
   def order(self):
      return parameter_order(self.name)
   
   #-- A parameter belongs to a system, and will be deleted if the system
   #   is deleted.
   star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- a parameter can belong to a dataset or datatable, but doesn't have too. 
   #   However, if it does belong to one, it has to be removed if the
   #   datasource is removed.
   data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- name of the variable measured in this parameter
   name = models.CharField(max_length=50)
   
   #-- component the parameter belongs to
   component = models.IntegerField(
      choices=COMPONENT_CHOICES,
      default=SYSTEM)
   
   #-- add component behind name if component is primary or secondry
   def cname(self):
      if self.component in [PRIMARY, SECONDARY]:
         return self.name + '_' + str(self.component)
      else:
         return self.name
   
   value = models.FloatField(default=0.0)
   
   #-- errors are stored as upper and lower error, and error function is 
   #   provided to return the average error in 1 value.
   #   the error field can also be directly set and will populate the
   #   error_l and _u field with the save value.
   error_l = models.FloatField(default=0.0)  # lower error
   error_u = models.FloatField(default=0.0)  # upper error
   
   @property
   def error(self):
      # return the error based on lower and upper error
      return (self.error_l + self.error_u) / 2.0
   
   @error.setter
   def error(self, val):
      # set  lower and upper error to the error value
      self.error_l = val
      self.error_u = val
   
   #-- unit in which this variable is measured
   unit = models.CharField(max_length=50)
   
   #-- valid setting to indicate wether or not this parameter is trustworthy
   valid = models.BooleanField(default=True)
   
   #-- set average=True to indicate this parameter contains the average
   #   of all measurements of this variable for this star. This average
   #   parameter is automatically created and updated upon saving a parameter
   average = models.BooleanField(default=False)
   
   #-- Rounded value and errors
   def rvalue(self):
      return round_value(self.value, self.name)
   
   def rerror(self):
      return round_value(self.error, self.name)
   
   def rerror_l(self):
      return round_value(self.error_l, self.name)
   
   def rerror_u(self):
      return round_value(self.error_u, self.name)
   
   
   #-- representation of self
   def __str__(self):
      return "{} = {} +- {} {} -{}- ({})".format(self.cname(), self.rvalue(), self.rerror(), 
                                          self.unit, 'V' if self.valid else 'F',
                                          self.data_source.name[0:10])

#@python_2_unicode_compatible  # to support Python 2
class DerivedParameter(Parameter):
   """
   Subtype of an average parameter that is derived based on other parameters
   """
   
   source_parameters = models.ManyToManyField(Parameter, blank=True, related_name='derived_parameters')
   
   def update(self):
      M = self.source_parameters.get(name__exact='mass')
      g = self.source_parameters.get(name__exact='logg')
      
      G = 6.673839999999998e-05
      M = np.random.normal(M.value, M.error, 512)
      g = np.random.normal(g.value, g.error, 512)
      r = np.sqrt(G * M * 1.988547e+30 / 10**g) / 69550800000.0
      
      self.name = 'radius'
      self.value = np.average(r)
      self.error = np.std(r)
      self.unit = 'Rsol'
      self.component = 1
      self.average = True
      
   #def __str__(self):
      #return "Derived parameter"
      
   #def save(self, *args, **kwargs):
      #super(DerivedParameter, self).save(*args, **kwargs)
      #self.update()
      #super(DerivedParameter, self).save(*args, **kwargs)
   
   

#======================================================================================
# AVERAGE parameter handling
#======================================================================================

def calculate_average(params):
   """
   Calculates the average value and error based on the given parameters
   params needs to be a queryset
   """
   values = np.array( params.values_list('value', flat=True) )
   
   #-- work with 1D average errors
   errors_l = np.array( params.values_list('error_l', flat=True) )
   errors_u = np.array( params.values_list('error_u', flat=True) )
   errors = (errors_l + errors_u) / 2.0
   
   #-- if the error is zero, assume a 10% error when calculating the average,
   #   if also the value is zero, assume an error of 1.
   errors = np.where(errors == 0, values / 10., errors)
   errors = np.where(errors == 0, 1., errors)
   
   error = np.sqrt(np.sum(errors**2)) / len(errors)
   
   return np.average(values, weights=1./errors), error

@receiver(post_delete, sender=Parameter)
@receiver(post_save, sender=Parameter)
def average_parameter_bookkeeping(sender, **kwargs):
   """
   Create, update and delete average parameters when parameters
   are added, updated, or deleted.
   """
   
   if kwargs.get('raw', False):
      return
   
   param = kwargs['instance']
   
   if not param.average:
      p = Parameter.objects.filter(name__exact      = param.name, 
                                   component__exact = param.component,
                                   star__exact      = param.star, 
                                   valid__exact     = True,
                                   average__exact   = False)
      
      
      if len(p) == 0:
         # There are no parameters left: delete the average
         try:
            ap = Parameter.objects.get(name__exact      = param.name, 
                                       component__exact = param.component,
                                       star__exact      = param.star, 
                                       valid__exact     = True,
                                       average__exact   = True)
            ap.delete()
         except Exception, e:
            pass
         
      else:
         # We need to update the average, or possible create a new one
         value, error = calculate_average(p)
         
         try:
            ap = Parameter.objects.get(name__exact      = param.name, 
                                       component__exact = param.component,
                                       star__exact      = param.star, 
                                       valid__exact     = True,
                                       average__exact   = True)
            ap.value = value
            ap.error = error
            ap.save()
            
         except Parameter.DoesNotExist:
            
            try:
               ds = DataSource.objects.get(name__exact='AVG')
            except DataSource.DoesNotExist:
               ds = DataSource.objects.create(name='AVG')
            
            ap = Parameter.objects.create(star        = param.star, 
                                          name        = param.name, 
                                          component   = param.component, 
                                          value       = value, 
                                          error       = error, 
                                          unit        = param.unit,
                                          average     = True, 
                                          valid       = True, 
                                          data_source = ds)
            

#======================================================================================
# DERIVED parameter handling
#======================================================================================

#@receiver(post_init, sender=DerivedParameter)
#def derived_parameter_find_sources(sender, **kwargs):
   #"""
   #When a new Derived parameter is created, find all necesary parameters
   #to derive it from
   #"""
   #pass
   