#from __future__ import unicode_literals

from django.db import models

from django.db.models.signals import pre_delete, post_delete, post_save, pre_save, post_init
from django.dispatch import receiver

from six import python_2_unicode_compatible

from stars.models import Star
from .datasource import  DataSource, AverageDataSource

from analysis.auxil import parameter_derivation

import numpy as np

#-- all constants are the roud_value function are imported from default values
from .default_values import *


def combine_parameter_name(name, component):

   if component in [1,2]:
      return name + '_' + str(component)
   else:
      return name





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
   cname = models.CharField(max_length=52, default='')

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
      return round_value(self.value, self.name, self.error)

   def rerror(self):
      return round_value(self.error, self.name, self.error)

   def rerror_l(self):
      return round_value(self.error_l, self.name, self.error_l)

   def rerror_u(self):
      return round_value(self.error_u, self.name, self.error_u)


   #-- representation of self
   def __str__(self):
      try:
         ds = self.data_source.name[0:10]
      except DataSource.DoesNotExist:
         ds = ''
      return "{} = {} +- {} {} -{}- ({})".format(self.cname, self.rvalue(), self.rerror(),
                                          self.unit, 'V' if self.valid else 'F', ds)

#@python_2_unicode_compatible  # to support Python 2
class DerivedParameter(Parameter):
   """
   Subtype of an average parameter that is derived based on other parameters
   """

   source_parameters = models.ManyToManyField(Parameter, blank=True, related_name='derived_parameters')

   def create(self):
      success = parameter_derivation.find_parameters(self)
      #try:
         #names, components = parameter_derivation.find_parameters(self)
         #for n, c in zip(names, components):
            #p = Parameter.objects.get(star__exact=self.star, name__exact=n,
                              #component__exact=c, average__exact=True)
            #self.source_parameters.add(p)

      #except Exception as e:
         #print (e)

   def update(self):
      try:
         parameter_derivation.calculate(self)
         self.average = True

         return True
      except Exception as e:
         print (e)

         return False

   #-- representation of self
   def __str__(self):
      return "{} = {} +- {} {} -{}- ({})".format(self.cname, self.rvalue(), self.rerror(),
                                          self.unit, 'V' if self.valid else 'F', 'DRVD')



#======================================================================================
# cname parameter handling
#======================================================================================

@receiver(pre_save, sender=Parameter)
@receiver(pre_save, sender=DerivedParameter)
def set_cname(sender, **kwargs):
   """
   When a parameter is created or modified, update the cname based on the
   parameter name and the component number:
   cname = name + _ + component if component is 1 or 2.
   """
   if kwargs.get('raw', False):
      return

   param = kwargs['instance']
   param.cname = combine_parameter_name(param.name, param.component)

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

   try:
      s = param.star
   except Star.DoesNotExist:
      #-- this star is being deleted along with all related parameters, do nothing
      return

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
         except Exception as e:
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

            #-- first get the datasource containing the average parameters
            try:
               ds = AverageDataSource.objects.get(project__exact=param.star.project)
            except AverageDataSource.DoesNotExist:
               ds = AverageDataSource.objects.create(name='AVG', project=param.star.project)

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


@receiver(pre_save, sender=DerivedParameter)
def derived_parameter_update_on_save(sender, **kwargs):
   """
   When a derived parameter is saved, update its value and error first.
   """
   if kwargs['raw']: return

   param = kwargs['instance']
   if not param._state.adding:
      # only update parameter if it is modified, not on creation
      success = param.update()

      if not success:
         param.delete()


@receiver(post_save, sender=DerivedParameter)
def derived_parameter_find_sources_on_create(sender, **kwargs):
   """
   When a new Derived parameter is created, find all necesary parameters
   to derive it from
   """
   param = kwargs['instance']

   #-- if the derived paramter is newly created, search for the needed parameters
   #   to calculate it.
   if kwargs['created']:
      param.create()
      param.save()




#@receiver(post_delete, sender=Parameter)
@receiver(post_save, sender=Parameter)
def derived_parameter_bookkeeping_on_update(sender, **kwargs):
   """
   Check if there are any derived parameters using this parameter,
   and if so, update theire values
   """
   if kwargs.get('raw', False):
      return

   param = kwargs['instance']

   if param.derived_parameters.exists():
      # Update derived parameters if there are any
      for p in param.derived_parameters.all():
         p.save()


@receiver(pre_delete, sender=Parameter)
def derived_parameter_bookkeeping_on_delete(sender, **kwargs):
   """
   Check if there are any derived parameters using this parameter,
   and if so, update theire values
   """
   if kwargs.get('raw', False):
      return

   param = kwargs['instance']

   if param.derived_parameters.exists():
      # Update derived parameters if there are any
      for p in param.derived_parameters.all():
         p.delete()
