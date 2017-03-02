from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from stars.models import Star

from .aux import plot_datasets

import numpy as np
from ivs.io import hdf5


#-- Method related constants
GENERIC = 'gen'
SED = 'sed'
PLOT_CHOISES = (
   (GENERIC, 'Generic'),
   (SED, 'SED hdf5'),)


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

class Method(models.Model):
   """
   This class represents different types of analysis methods, so that new ones
   can be added without the need to change the source code.
   """
   
   name = models.TextField(default='')
   description = models.TextField(default='')
   
   #-- short name for the method without spaces. To be used in determining 
   #   the method used in uploaded files
   slug = models.SlugField(max_length=10, default='', unique=True)
   
   color = models.CharField(max_length=7, default='#8B0000') # color as hex color value
   
   #-- plot type defines what the structure of the hdf5 file is
   data_type = models.CharField(max_length=7, choices=PLOT_CHOISES, default=GENERIC)
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   #-- representation of self
   def __str__(self):
      return "{} - {}".format(self.name, self.description)
   
   #-- set the slug on save if it is empty
   def save(self, **kwargs):
      if self.slug == '':
         self.slug = self.name.replace(" ", "")
      super(Method, self).save(**kwargs)

class DataSet(models.Model):
   
   #-- the dataset belongs to one star, and is deleted when the star is
   #   removed.
   star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)
   
   name = models.TextField(default='')
   note = models.TextField(default='')
   
   method = models.ForeignKey(Method, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- the actual results are stored in a hdf5 file
   datafile = models.FileField(upload_to='datasets/')
   
   #-- valid setting to indicate wether or not this dataset is trustworthy
   valid = models.BooleanField(default=True)
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   def get_data(self):
      return hdf5.read2dict(self.datafile.path)
   
   def make_figure(self):
      """
      Method for returning the bokeh figure showing the results 
      of this dataset.
      """
      return plot_datasets.plot_dataset(self.datafile.path, self.method)
   
   def make_large_figure(self):
      """
      Method for returning a large bokeh figure showing the results 
      of this dataset.
      """
      return plot_datasets.plot_dataset_large(self.datafile.path, self.method)
   
   def make_parameter_CI_figures(self):
      """
      Returns a figure for each parameters that has confidence interval information
      """
      return plot_datasets.plot_parameter_ci(self.datafile.path, self.method)
   
   def get_system_parameters(self):
      """
      Returns a list of parameters that describe a property of the
      system, as for example orbital period or reddening.
      The list contains a tupple of (parameter name, unit, value+-error)
      for each parameter
      """
      parameters = self.parameter_set.filter(component__exact=SYSTEM)
      pars = []
      for p in parameters.order_by('name'):
         prec = PARAMETER_DECIMALS.get(p.name, 3)
         pars.append( (p.name, p.unit, "{: > 6.{prec}f} &pm; {: > 6.{prec}f}".format(p.rvalue(), p.rerror(), prec=prec) ) ) 
      return pars
   
   def get_component_parameters(self):
      """
      Returns a list of parameters that describe a property of one of
      the components of the system, as effective temperature or logg.
      The list contains a tupple of (parameter name, unit, v1+-e1, v2+-e2)
      for each parameter
      """
      parameters = set(self.parameter_set.filter(component__in=STELLAR_PARAMETERS).values_list('name', flat=True))
      pars = []
      for pname in parameters:
         qset = self.parameter_set.filter(name__exact=pname) # need to use filter here not get!
         
         line = [pname, qset[0].unit]
         for comp in STELLAR_PARAMETERS:
            p = qset.filter(component__exact = comp)
            
            if p:
               prec = PARAMETER_DECIMALS.get(p[0].name, 3)
               line.append("{: > 5.{prec}f} &pm; {: > 5.{prec}f}".format(p[0].rvalue(), 
                                                                         p[0].rerror(), prec=prec))
            else:
               line.append(r" / ")
               
         pars.append( tuple(line) )
      return pars

class DataTable(models.Model):
   
   #-- the table is stored in a txt file
   datafile = models.FileField(upload_to='datatables/')
   
   name = models.TextField(default='')
   note = models.TextField(default='')
   
   #-- ';' separated list of the column names, each name should correspond
   #   with a recognizable parameter name.
   columnnames = models.TextField(default='')
   
   #-- table dimentions
   xdim = models.IntegerField(default=0)
   ydim = models.IntegerField(default=0)
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)



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
   #   datasetdatatable is removed.
   data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, blank=True, null=True)
   data_table = models.ForeignKey(DataTable, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- using properties to change the output of the name to the correct value
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
   
   value = models.FloatField()
   
   error_l = models.FloatField(default=0.0)  # lower error
   error_u = models.FloatField(default=0.0)  # upper error
   
   #-- valid setting to indicate wether or not this parameter is trustworthy
   valid = models.BooleanField(default=True)
   
   @property
   def error(self):
      # return the error based on lower and upper error
      return (self.error_l + self.error_u) / 2.0
   
   @error.setter
   def error(self, val):
      # set  lower and upper error to the error value
      self.error_l = val
      self.error_u = val
   
   unit = models.CharField(max_length=50)
   
   #-- Rounded value and errors
   def rvalue(self):
      return round_value(self.value, self.name)
   
   def rerror(self):
      return round_value(self.error, self.name)
   
   def rerror_l(self):
      return round_value(self.error_l, self.name)
   
   def rerror_u(self):
      return round_value(self.error_u, self.name)
   
   
@receiver(post_delete, sender=DataSet)
def dataSet_post_delete_handler(sender, **kwargs):
    analmethod = kwargs['instance']
    storage, path = analmethod.datafile.storage, analmethod.datafile.path
    storage.delete(path)