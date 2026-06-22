from unittest.mock import patch

import numpy as np
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.models import ParameterSource
from analysis.services import parameter_io
from analysis.services.consensus_defaults import seed_project_consensus_policies
from analysis.services.parameter_consensus import sync_consensus_cache
from dash.starmap_plotting import plot_interactive_starmap
from stars.models import Project, Star
from stars.services.starmap import (
    build_aitoff_grid,
    collect_star_positions,
    galactic_aitoff_xy,
    starmap_metadata,
    starmap_star_records,
)
from stars.tasks import fetch_gaia_bulk_task

User = get_user_model()


class StarmapServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='StarmapTest', slug='starmap-test', description='')
        seed_project_consensus_policies(self.project)

    def _create_star(self, name='StarA', ra=120.0, dec=30.0):
        return Star.objects.create(
            name=name,
            project=self.project,
            ra=ra,
            dec=dec,
        )

    def test_metadata_without_parallax(self):
        self._create_star()
        metadata = starmap_metadata(self.project)

        self.assertFalse(metadata['colored_by_distance'])
        self.assertEqual(metadata['n_stars'], 1)

    def test_metadata_with_consensus_parallax(self):
        star = self._create_star()
        source = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        parameter_io.create_measurement(
            star=star,
            name='parallax',
            value=5.0,
            error_l=0.05,
            error_u=0.05,
            unit='mas',
            parameter_source=source,
        )
        sync_consensus_cache(star, 'parallax', 0)

        metadata = starmap_metadata(self.project)

        self.assertTrue(metadata['colored_by_distance'])
        positions = collect_star_positions(self.project)
        self.assertEqual(len(positions), 1)
        self.assertAlmostEqual(positions[0].parallax_mas, 5.0)

    def test_consensus_parallax_not_raw_lower_priority_source(self):
        star = self._create_star()
        dr2 = ParameterSource.objects.create(name='Gaia DR2', project=self.project)
        dr3 = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        parameter_io.create_measurement(
            star=star,
            name='parallax',
            value=1.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=dr2,
        )
        parameter_io.create_measurement(
            star=star,
            name='parallax',
            value=8.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=dr3,
        )
        sync_consensus_cache(star, 'parallax', 0)

        positions = collect_star_positions(self.project)

        self.assertAlmostEqual(positions[0].parallax_mas, 8.0)

    def test_galactic_aitoff_xy_returns_finite_coords(self):
        x, y = galactic_aitoff_xy([30.0, 120.0], [10.0, -20.0])
        self.assertEqual(len(x), 2)
        self.assertTrue(np.all(np.isfinite(x)))
        self.assertTrue(np.all(np.isfinite(y)))

    def test_build_aitoff_grid_has_meridians_and_labels(self):
        grid = build_aitoff_grid()
        self.assertEqual(len(grid.meridian_xs), 12)
        self.assertEqual(len(grid.parallel_xs), 10)
        self.assertEqual(len(grid.longitude_tick_labels), 12)
        self.assertGreater(len(grid.outline_xs), 10)
        self.assertGreater(max(grid.outline_xs), 1.5)
        for xs, ys in zip(grid.parallel_xs, grid.parallel_ys):
            seg = np.sqrt(np.diff(xs) ** 2 + np.diff(ys) ** 2)
            self.assertLess(seg.max(), 0.05)

    def test_starmap_star_records_include_galactic_fields(self):
        self._create_star()
        records = starmap_star_records(self.project)
        self.assertEqual(len(records), 1)
        self.assertIn('l', records[0])
        self.assertIn('b', records[0])
        self.assertIn('/systems/stars/', records[0]['url'])

    def test_plot_interactive_starmap_returns_figure(self):
        self._create_star()
        figure = plot_interactive_starmap(self.project)
        self.assertIsNotNone(figure)
        self.assertGreater(len(figure.renderers), 0)


class StarmapApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name='DashStarmap',
            slug='dash-starmap',
            description='',
            is_public=True,
        )
        seed_project_consensus_policies(self.project)
        Star.objects.create(name='S1', project=self.project, ra=10.0, dec=10.0)
        self.viewer = User.objects.create_user(username='viewer', password='testpass123')
        self.project.readonly_users.add(self.viewer)

    def test_get_starmap_public(self):
        response = self.client.get(f'/api/dash/{self.project.slug}/starmap/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('n_stars', response.data)
        self.assertIn('interactive', response.data)
        self.assertIsNotNone(response.data['interactive'])
        self.assertNotIn('preview_url', response.data)

    def test_get_starmap_accepts_theme_query(self):
        for theme in ('dark', 'light', 'invalid'):
            response = self.client.get(f'/api/dash/{self.project.slug}/starmap/?theme={theme}')
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.data['interactive'])

    def test_get_starmap_json_format(self):
        response = self.client.get(f'/api/dash/{self.project.slug}/starmap/?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['stars']), 1)
        self.assertIn('url', response.data['stars'][0])
        self.assertIn('l', response.data['stars'][0])

    def test_get_starmap_private_forbidden_for_anonymous(self):
        self.project.is_public = False
        self.project.save(update_fields=['is_public'])
        response = self.client.get(f'/api/dash/{self.project.slug}/starmap/')
        self.assertEqual(response.status_code, 403)

    def test_dashboard_bootstrap_omits_starmap(self):
        response = self.client.get(f'/api/dash/{self.project.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('starmap', response.data)


class GaiaBulkTaskTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Schedule', slug='schedule', description='')

    @patch('stars.tasks.import_gaia_dr3_for_star')
    def test_gaia_bulk_completes_without_starmap_regeneration(self, mock_import):
        from stars.services.gaia_import import GaiaImportResult

        star = Star.objects.create(name='G1', project=self.project, ra=1.0, dec=1.0)
        mock_import.return_value = GaiaImportResult(status='ok', message='ok', fields_updated=[])

        with patch.object(fetch_gaia_bulk_task, 'update_state'):
            summary = fetch_gaia_bulk_task.run(self.project.pk, [star.pk], None)

        self.assertEqual(summary['ok'], 1)
