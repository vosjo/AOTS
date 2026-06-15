import numpy as np
from django.test import TestCase

from analysis.auxil import parameter_derivation
from analysis.models import DerivedParameter, Parameter, ParameterSource
from analysis.services.parameter_sources import get_or_create_avg_source
from stars.models import Project, Star


class DerivationMathTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='DerivTest', description='')
        self.star = Star.objects.create(
            name='Test', project=self.project, ra=1.0, dec=2.0,
        )

    def test_calculate_q(self):
        ds = ParameterSource.objects.create(name='src', project=self.project)
        Parameter.objects.create(
            star=self.star, name='K', component=1, value=5.0, error=0.5,
            unit='km/s', parameter_source=ds,
        )
        Parameter.objects.create(
            star=self.star, name='K', component=2, value=10.0, error=1.0,
            unit='km/s', parameter_source=ds,
        )
        avg = get_or_create_avg_source(self.project)
        dpar = DerivedParameter.objects.create(
            star=self.star, name='q', component=0, average=True, parameter_source=avg,
        )
        self.assertTrue(parameter_derivation.find_parameters(dpar))
        parameter_derivation.calculate(dpar)
        self.assertAlmostEqual(dpar.value, 0.5, places=1)

    def test_calculate_r(self):
        ds = ParameterSource.objects.create(name='src', project=self.project)
        Parameter.objects.create(
            star=self.star, name='m', component=1, value=1.0, error=0.1,
            unit='Msol', average=True, parameter_source=ds,
        )
        Parameter.objects.create(
            star=self.star, name='logg', component=1, value=4.0, error=0.1,
            unit='cgs', average=True, parameter_source=ds,
        )
        avg = get_or_create_avg_source(self.project)
        dpar = DerivedParameter.objects.create(
            star=self.star, name='r', component=1, average=True, parameter_source=avg,
        )
        parameter_derivation.find_parameters(dpar)
        parameter_derivation.calculate(dpar)
        self.assertGreater(dpar.value, 0)
