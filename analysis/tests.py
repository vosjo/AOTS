from django.test import TestCase

import numpy as np

# Create your tests here.

from analysis.models import Parameter, DataSource
from stars.models import Star

class AverageParameter(TestCase):
   
   def setUp(self):
      
      s = Star.objects.create(name='test star', ra=1.1, dec=-10.3)
      
      ds1 = DataSource.objects.create(name='tc 1')
      ds2 = DataSource.objects.create(name='tc 2')
      
      Parameter.objects.create(star=s, name='teff', component=1, value=30000, error=5000, unit='K', data_source=ds1)
      
      Parameter.objects.create(star=s, name='teff', component=1, value=35000, error=3000, unit='K', data_source=ds2)
   
   
   def test_average_parameter_create(self):
      """
      On parameter creation, the average parameter needs to be updated
      """
      p = Parameter.objects.get(name__exact='teff', average__exact=True)
      
      self.assertEqual(np.round(p.value, 0), 33125, 
                       "Average creation: value is wrong {}".format(p) )
      self.assertEqual(np.round(p.error, 1), np.round(np.sqrt(3000.**2+5000.**2)/2., 1),
                       "Average creation: error is wrong {}".format(p) )
   
   
   def test_average_parameter_on_parameter_update(self):
      """
      Invalid parameters need to be ignored when calculating average parameter
      """
      p = Parameter.objects.get(value__exact=35000, average__exact=False)
      p.value = 34000
      p.error = 2000
      p.save()
      
      p = Parameter.objects.get(name__exact='teff', average__exact=True)
      self.assertEqual(np.round(p.value, 0), 32857,
                       "Average update: value is wrong {}".format(p) ) 
      self.assertEqual(np.round(p.error, 1), np.round(np.sqrt(2000.**2+5000.**2)/2., 1),
                       "Average update: error is wrong {}".format(p) ) 
   
   
   def test_average_parameter_on_invalid_parameters(self):
      """
      Invalid parameters need to be ignored when calculating average parameter
      """
      p = Parameter.objects.get(value__exact=35000, average__exact=False)
      p.valid = False
      p.save()
      
      p = Parameter.objects.get(name__exact='teff', average__exact=True)
      self.assertEqual(np.round(p.value, 0), 30000,
                       "Average invalid parameter: value is wrong {}".format(p) ) 
      self.assertEqual(np.round(p.error, 0), 5000,
                       "Average invalid parameter: error is wrong {}".format(p) ) 
      
      
   def test_average_parameter_update_on_parameter_delete(self):
      """
      If a parameter is removed, the average value needs to be recomputed
      """
      p = Parameter.objects.get(value__exact=30000, average__exact=False)
      p.delete()
      
      p = Parameter.objects.get(name__exact='teff', average__exact=True)
      self.assertEqual(np.round(p.value, 0), 35000,
                       "Average on parameter delete: value is wrong {}".format(p) )
      self.assertEqual(np.round(p.error, 0), 3000,
                       "Average on parameter delete: error is wrong {}".format(p) )
      
      
   def test_average_parameter_delete_when_all_parameters_removed(self):
      """
      If all parameters are removed, the average parameter needs to be
      removed as well.
      """
      p = Parameter.objects.get(value__exact=30000, average__exact=False)
      p.delete()
      
      p = Parameter.objects.get(value__exact=35000, average__exact=False)
      p.delete()
      
      p = Parameter.objects.filter(name__exact='teff', average__exact=True)
      self.assertEqual(len(p), 0, 
                       "Average on no parameters left: average should have been deleted" )
      
      
      
   #def tearDown(self):
      
      #Star.objects.all().delete()
      #DataSource.objects.all().delete()
      #Parameter.objects.all().delete()