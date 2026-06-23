from unittest.mock import Mock

from django.test import TestCase

from analysis.models import ParameterSource
from analysis.services import parameter_io
from analysis.services.consensus_defaults import seed_project_consensus_policies
from dash.plotting import _MISSING, plot_hrd
from stars.models import Project, Star


class PlotHrdConsensusTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='HRD', description='')
        seed_project_consensus_policies(self.project)
        self.star = Star.objects.create(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )
        self.gaia = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        for name, value, error in (
            ('mag', 10.5, 0.02),
            ('bp_rp', 1.2, 0.05),
            ('absolute_g_mag', 5.0, 0.1),
        ):
            parameter_io.create_measurement(
                star=self.star,
                name=name,
                value=value,
                error_l=error,
                error_u=error,
                unit='mag',
                parameter_source=self.gaia,
            )

    def test_plot_hrd_uses_consensus_not_photometry(self):
        self.assertEqual(self.star.photometry_set.count(), 0)

        request = Mock()
        fig = plot_hrd(
            request,
            self.project.pk,
            xstr='bp_rp',
            ystr='absolute_g_mag',
            nstars=1,
            theme='dark',
        )

        renderer = fig.select_one({'name': 'main'})
        self.assertIsNotNone(renderer)
        data = renderer.data_source.data
        self.assertAlmostEqual(data['bp_rp'][0], 1.2)
        self.assertAlmostEqual(data['absolute_g_mag'][0], 5.0)
        self.assertAlmostEqual(data['mag'][0], 10.5)
        self.assertNotEqual(data['bp_rp'][0], _MISSING)
