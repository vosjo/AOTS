import numpy as np
from django.test import TestCase

from analysis.models import DerivedParameter, Parameter, ParameterSource
from analysis.services import parameter_io
from analysis.services.parameter_sources import get_or_create_avg_source
from stars.models import Project, Star


class CnameParameter(TestCase):

    def setUp(self):
        p = Project.objects.create(name='TestCase', description='TestCase_description')
        self.star = Star.objects.create(
            name='Vega', project=p, ra=279.23473479, dec=38.78368896,
        )
        ds1 = ParameterSource.objects.create(name='tc 1', project=p)
        parameter_io.create_measurement(
            star=self.star, name='teff', component=1, value=30000,
            error_l=5000, error_u=5000, unit='K', parameter_source=ds1,
        )

    def test_cname_on_creation(self):
        p = Parameter.objects.get(name__exact='teff', average=False)
        self.assertEqual(p.cname, 'teff_1')

    def test_cname_on_modify(self):
        p = Parameter.objects.get(name__exact='teff', average=False)
        parameter_io.update_measurement(p, name='logg')
        self.assertEqual(p.cname, 'logg_1')
        parameter_io.update_measurement(p, component=2)
        self.assertEqual(p.cname, 'logg_2')


class AverageParameter(TestCase):

    def setUp(self):
        project = Project.objects.create(name='TestCase', description='TestCase_description')
        self.star = Star.objects.create(
            name='Vega', project=project, ra=279.23473479, dec=38.78368896,
        )
        ds1 = ParameterSource.objects.create(name='tc 1', project=project)
        ds2 = ParameterSource.objects.create(name='tc 2', project=project)
        parameter_io.create_measurement(
            star=self.star, name='teff', component=1, value=30000,
            error_l=5000, error_u=5000, unit='K', parameter_source=ds1,
        )
        parameter_io.create_measurement(
            star=self.star, name='teff', component=1, value=35000,
            error_l=3000, error_u=3000, unit='K', parameter_source=ds2,
        )

    def test_average_parameter_create(self):
        p = Parameter.objects.get(name__exact='teff', average__exact=True)
        self.assertEqual(np.round(p.value, 0), 33676)
        self.assertAlmostEqual(p.error, 2572.5, delta=0.1)

    def test_average_parameter_zero_error(self):
        s = Star.objects.get(name__exact='Vega')
        project = Project.objects.get(name__exact='TestCase')
        ds = ParameterSource.objects.create(name='tc 3', project=project)
        parameter_io.create_measurement(
            star=s, name='teff', component=1, value=32000,
            error_l=0, error_u=0, unit='K', parameter_source=ds,
        )
        p = Parameter.objects.get(name__exact='teff', average__exact=True)
        self.assertEqual(np.round(p.value, 0), 33018)

    def test_average_parameter_update(self):
        p = Parameter.objects.get(value__exact=35000, average__exact=False)
        parameter_io.update_measurement(p, value=36000, error_l=2000, error_u=2000)
        p = Parameter.objects.get(name__exact='teff', average__exact=True)
        self.assertEqual(np.round(p.value, 0), 35172)

    def test_average_parameter_update_error(self):
        p = Parameter.objects.get(value__exact=35000, average__exact=False)
        parameter_io.update_measurement(p, error_l=1000, error_u=1000)
        p = Parameter.objects.get(name__exact='teff', average__exact=True)
        self.assertAlmostEqual(p.error, 980.6, delta=0.1)

    def test_average_parameter_delete(self):
        project = Project.objects.create(name='DelAvg', description='')
        star = Star.objects.create(name='Solo', project=project, ra=0, dec=0)
        ds = ParameterSource.objects.create(name='tc', project=project)
        parameter_io.create_measurement(
            star=star, name='teff', component=1, value=30000,
            error_l=5000, error_u=5000, unit='K', parameter_source=ds,
        )
        p = Parameter.objects.get(star=star, value=30000, average=False)
        parameter_io.delete_measurement(p)
        with self.assertRaises(Parameter.DoesNotExist):
            Parameter.objects.get(star=star, name='teff', average=True)

    def test_average_parameter_delete_one_of_two(self):
        p = Parameter.objects.get(value__exact=30000, average__exact=False)
        parameter_io.delete_measurement(p)
        p = Parameter.objects.get(value__exact=35000, average__exact=False)
        self.assertEqual(p.value, 35000)
        p = Parameter.objects.get(name__exact='teff', average__exact=True)
        self.assertEqual(np.round(p.value, 0), 35000)


class DerivedParameterTests(TestCase):

    def setUp(self):
        p = Project.objects.create(name='TestCase', description='TestCase_description')
        s = Star.objects.create(
            name='Vega', project=p, ra=279.23473479, dec=38.78368896,
        )
        ds1 = ParameterSource.objects.create(name='tc 1', project=p)
        ds2 = ParameterSource.objects.create(name='tc 2', project=p)
        parameter_io.create_measurement(
            star=s, name='mass', component=1, value=0.47,
            error_l=0.05, error_u=0.05, unit='Msol', parameter_source=ds1,
        )
        parameter_io.create_measurement(
            star=s, name='K', component=1, value=5.5,
            error_l=0.5, error_u=0.5, unit='km s-1', parameter_source=ds1,
        )
        parameter_io.create_measurement(
            star=s, name='K', component=2, value=13.8,
            error_l=1.2, error_u=1.2, unit='km s-1', parameter_source=ds1,
        )
        parameter_io.create_measurement(
            star=s, name='logg', component=1, value=5.80,
            error_l=0.20, error_u=0.20, unit='cgs', parameter_source=ds2,
        )

    def test_derived_parameter_create(self):
        s = Star.objects.get(name__exact='Vega')
        p = parameter_io.create_derived_record(
            star=s, project=s.project, name='q', component=0,
        )
        self.assertIsNotNone(p)
        self.assertEqual(len(p.source_parameters.all()), 2)
        self.assertEqual(np.round(p.value, 1), 0.4)
        self.assertEqual(np.round(p.error, 2), 0.05)

    def test_derived_parameter_update_on_parameter_save(self):
        s = Star.objects.get(name__exact='Vega')
        parameter_io.create_derived_record(star=s, project=s.project, name='q', component=0)
        k1 = Parameter.objects.get(
            star__exact=s, name__exact='K', component__exact=1, average__exact=False,
        )
        parameter_io.update_measurement(k1, value=3.0, error_l=0.3, error_u=0.3)
        p = DerivedParameter.objects.get(
            star__exact=s, name__exact='q', average__exact=True, component__exact=0,
        )
        self.assertEqual(np.round(p.value, 1), 0.2)
        self.assertEqual(np.round(p.error, 2), 0.03)

    def test_derived_parameter_delete_on_parameter_delete(self):
        s = Star.objects.get(name__exact='Vega')
        parameter_io.create_derived_record(star=s, project=s.project, name='q', component=0)
        k1 = Parameter.objects.get(
            star__exact=s, name__exact='K', component__exact=1, average__exact=False,
        )
        parameter_io.delete_measurement(k1)
        with self.assertRaises(DerivedParameter.DoesNotExist):
            DerivedParameter.objects.get(
                star__exact=s, name__exact='q', average__exact=True, component__exact=0,
            )


class ParameterIoSignalFreeTests(TestCase):
    def test_raw_orm_create_skips_bookkeeping(self):
        project = Project.objects.create(name='RawORM', description='')
        star = Star.objects.create(name='S', project=project, ra=0, dec=0)
        src = ParameterSource.objects.create(name='src', project=project)
        Parameter.objects.create(
            star=star, name='teff', component=0, value=5000,
            error_l=100, error_u=100, unit='K', parameter_source=src,
        )
        self.assertFalse(
            Parameter.objects.filter(star=star, name='teff', average=True).exists(),
        )
