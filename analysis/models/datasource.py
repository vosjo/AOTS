from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from stars.models import Star

from analysis.aux import plot_datasets

import numpy as np
from analysis.aux import fileio


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
   
   #--automatically derived parameters stored as ',' separated string
   derived_parameters = models.TextField(default='')
   
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


class DataSource(models.Model):
   """
   Super class for any object that has parameters attached.
   """
   
   name = models.TextField(default='')
   note = models.TextField(default='')
   reference = models.TextField(default='')
   
   #-- bookkeeping
   added_on = models.DateTimeField(auto_now_add=True)
   last_modified = models.DateTimeField(auto_now=True)
   
   def source(self):
      """
      Retruns a string representation of the source of the parameters
      depending on whether this object is a DataSet, DataTable or 
      a random source
      """
      try:
         return self.dataset.method.name
      except DataSet.DoesNotExist:
         return self.reference if self.reference != '' else self.name
   
   #-- representation of self
   def __str__(self):
      return "{} {}".format(self.name, '({})'.format(self.reference) if self.reference else '')
   
class DataTable(DataSource):
   
   #-- the table is stored in a txt file
   datafile = models.FileField(upload_to='datatables/')
   
   #-- ';' separated list of the column names, each name should correspond
   #   with a recognizable parameter name.
   columnnames = models.TextField(default='')
   
   #-- table dimentions
   xdim = models.IntegerField(default=0)
   ydim = models.IntegerField(default=0)

class DataSet(DataSource):
   
   #-- the dataset belongs to one star, and is deleted when the star is
   #   removed.
   star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- analysis method used for this dataset
   method = models.ForeignKey(Method, on_delete=models.CASCADE, blank=True, null=True)
   
   #-- the actual results are stored in a hdf5 file
   datafile = models.FileField(upload_to='datasets/')
   
   #-- valid setting to indicate wether or not this dataset is trustworthy
   valid = models.BooleanField(default=True)
   
   
   def get_data(self):
      return fileio.read2dict(self.datafile.path)
   
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
   
   
@receiver(post_delete, sender=DataSet)
def dataSet_post_delete_handler(sender, **kwargs):
    analmethod = kwargs['instance']
    storage, path = analmethod.datafile.storage, analmethod.datafile.path
    storage.delete(path)