from django.test import TestCase

import numpy as np

from analysis.models import Parameter, DerivedParameter, DataSource
from stars.models import Star, Project

class CnameParameter(TestCase):

   def setUp(self):

      p = Project.objects.create(
          name='TestCase',
          description='TestCase_description',
          )
      s = Star.objects.create(
          name='Vega',
          project=p,
          ra=279.23473479,
          dec=38.78368896,
          )

      ds1 = DataSource.objects.create(name='tc 1', project=p)

      Parameter.objects.create(star=s, name='teff', component=1, value=30000, error=5000, unit='K', data_source=ds1)

   def test_cname_on_creation(self):
      """
      On parameter creation the cname needs to be set correctly
      """
      p = Parameter.objects.get(name__exact='teff', average=False)

      self.assertEqual(p.cname, 'teff_1',
                       "cname on create not correct: {}, should be teff_1".format(p.cname))

   def test_cname_on_modify(self):
      """
      On parameter modify the cname needs to be updated if the
      name or component is changed.
      """
      p = Parameter.objects.get(name__exact='teff', average=False)
      p.name = 'logg'
      p.save()

      self.assertEqual(p.cname, 'logg_1',
                       "cname on name modify not correct: {}, should be logg_1".format(p.cname))

      p.component = 2
      p.save()

      self.assertEqual(p.cname, 'logg_2',
                       "cname on comp. modify not correct: {}, should be logg_2".format(p.cname))


class AverageParameter(TestCase):

   def setUp(self):

      project = Project.objects.create(
          name='TestCase',
          description='TestCase_description',
          )
      s = Star.objects.create(
          name='Vega',
          project=project,
          ra=279.23473479,
          dec=38.78368896,
          )

      ds1 = DataSource.objects.create(name='tc 1', project=project)
      ds2 = DataSource.objects.create(name='tc 2', project=project)

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

   def test_average_parameter_zero_error(self):
      """
      If a parameter has an error of 0, when calculating the average, an
      error of 10% of the value is assumed
      """
      s       = Star.objects.get(name__exact='Vega')
      project = Project.objects.get(name__exact='TestCase')
      ds      = DataSource.objects.create(name='tc 3', project=project)

      Parameter.objects.create(star=s, name='teff', component=1, value=32000, error=0, unit='K', data_source=ds)

      p = Parameter.objects.get(name__exact='teff', average__exact=True)

      self.assertEqual(np.round(p.value, 0), 32709,
                       "Average zero error: value is wrong {}".format(p) )
      self.assertEqual(np.round(p.error, 1), np.round(np.sqrt(3000.**2+5000.**2 + 3200**2)/3., 1),
                       "Average zero error: error is wrong {}".format(p) )

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



class DeriveParameters(TestCase):

   def setUp(self):

      p = Project.objects.create(
          name='TestCase',
          description='TestCase_description',
          )
      s = Star.objects.create(
          name='Vega',
          project=p,
          ra=279.23473479,
          dec=38.78368896,
          )

      ds1 = DataSource.objects.create(name='tc 1', project=p)
      ds2 = DataSource.objects.create(name='tc 2', project=p)

      Parameter.objects.create(star=s, name='mass', component=1, value=0.47, error=0.05, unit='Msol', data_source=ds1)

      Parameter.objects.create(star=s, name='K', component=1, value=5.5, error=0.5, unit='km s-1', data_source=ds1)

      Parameter.objects.create(star=s, name='K', component=2, value=13.8, error=1.2, unit='km s-1', data_source=ds1)

      Parameter.objects.create(star=s, name='logg', component=1, value=5.80, error=0.20, unit='cgs', data_source=ds2)


   def test_derived_parameter_create(self):
      """
      On parameter creation, the average parameter needs to be instantiated and calculated
      """
      s = Star.objects.get(name__exact='Vega')

      try:
         ds = DataSource.objects.get(name__exact='AVG')
      except DataSource.DoesNotExist:
         ds = DataSource.objects.create(name='AVG')

      p = DerivedParameter.objects.create(star=s, name='q', data_source=ds,
                                          average=True, component=0)

      source = p.source_parameters.all()
      self.assertEqual(len(source), 2,
                       "Source parameters not correctly loaded: {}".format(p.source_parameters.all()) )
      self.assertEqual(np.round(p.value, 1), 0.4,
                       "DerivedParamter on create: value is wrong {}".format(p) )
      self.assertEqual(np.round(p.error, 2), 0.05,
                       "DerivedParamter on create: error is wrong {}".format(p) )


   def test_derived_parameter_update_on_parameter_save(self):
      """
      When a parameter that is used to calculate a derived parameter is changed,
      the derived parameter needs to be changed
      """
      s = Star.objects.get(name__exact='Vega')

      try:
         ds = DataSource.objects.get(name__exact='AVG')
      except DataSource.DoesNotExist:
         ds = DataSource.objects.create(name='AVG')

      DerivedParameter.objects.create(star=s, name='q', data_source=ds,
                                          average=True, component=0)

      k1 = Parameter.objects.get(star__exact=s, name__exact='K',
                                 component__exact=1, average__exact=False)
      k1.value = 3.0
      k1.error = 0.3
      k1.save()

      p = DerivedParameter.objects.get(star__exact=s, name__exact='q',
                                       average__exact=True, component__exact=0)

      self.assertEqual(np.round(p.value, 1), 0.2,
                       "DerivedParamter on parameter update: value is wrong {}".format(p) )
      self.assertEqual(np.round(p.error, 2), 0.03,
                       "DerivedParamter on parameter update: error is wrong {}".format(p) )


   def test_derived_parameter_delete_on_parameter_delete(self):
      """
      When a parameter used to calculate a derived parameter is deleted, that derived
      parameter needs to be deleted as well.
      """
      s = Star.objects.get(name__exact='Vega')

      try:
         ds = DataSource.objects.get(name__exact='AVG')
      except DataSource.DoesNotExist:
         ds = DataSource.objects.create(name='AVG')

      DerivedParameter.objects.create(star=s, name='q', data_source=ds,
                                          average=True, component=0)

      k1 = Parameter.objects.get(star__exact=s, name__exact='K',
                                 component__exact=1, average__exact=False)
      k1.delete()

      with self.assertRaises(DerivedParameter.DoesNotExist,
                             msg="Derived parameter on parameter delete: should be deleted."):
         p = DerivedParameter.objects.get(star__exact=s,
                        name__exact='q', average__exact=True, component__exact=0)



