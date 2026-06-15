import numpy as np
from django.test import TestCase

from analysis.auxil import parameter_derivation
from analysis.models import DerivedParameter, ParameterSource
from analysis.services import parameter_io
from analysis.services.parameter_sources import get_or_create_avg_source
from stars.models import Project, Star


class DerivationMathTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='DerivTest', description='')
        self.star = Star.objects.create(
            name='Test', project=self.project, ra=1.0, dec=2.0,
        )

    def test_calculate_q_with_lowercase_k_from_hdf5(self):
        ds = ParameterSource.objects.create(name='src', project=self.project)
        parameter_io.create_measurement(
            star=self.star, name='k', component=1, value=5.0,
            error_l=0.5, error_u=0.5, unit='km/s', parameter_source=ds,
        )
        parameter_io.create_measurement(
            star=self.star, name='k', component=2, value=10.0,
            error_l=1.0, error_u=1.0, unit='km/s', parameter_source=ds,
        )
        dpar = parameter_io.create_derived_record(
            star=self.star, project=self.project, name='q', component=0,
        )
        self.assertIsNotNone(dpar)
        self.assertAlmostEqual(dpar.value, 0.5, places=1)

    def test_calculate_r(self):
        ds = ParameterSource.objects.create(name='src', project=self.project)
        avg = get_or_create_avg_source(self.project)
        parameter_io.create_measurement(
            star=self.star, name='m', component=1, value=1.0,
            error_l=0.1, error_u=0.1, unit='Msol', average=True, parameter_source=avg,
            run_after=False,
        )
        parameter_io.create_measurement(
            star=self.star, name='logg', component=1, value=4.0,
            error_l=0.1, error_u=0.1, unit='cgs', average=True, parameter_source=avg,
            run_after=False,
        )
        dpar = parameter_io.create_derived_record(
            star=self.star, project=self.project, name='r', component=1,
        )
        self.assertIsNotNone(dpar)
        self.assertGreater(dpar.value, 0)
