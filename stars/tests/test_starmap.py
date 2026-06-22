from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.models import ParameterSource
from analysis.services import parameter_io
from analysis.services.consensus_defaults import seed_project_consensus_policies
from analysis.services.parameter_consensus import sync_consensus_cache
from stars.models import Project, Star
from stars.services.starmap import (
    collect_star_positions,
    generate_starmap,
    regenerate_all_starmaps,
    schedule_starmap_regeneration,
)
from stars.tasks import fetch_gaia_bulk_task, regenerate_all_starmaps_task

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

    def test_generate_without_parallax_uses_fallback(self):
        self._create_star()
        result = generate_starmap(self.project)

        self.assertFalse(result.colored_by_distance)
        self.assertEqual(result.n_stars, 1)
        self.assertTrue(self.project.preview_starmap.name)
        self.assertTrue(self.project.full_starmap.name)
        self.assertIsNotNone(self.project.starmap_generated_at)

    def test_generate_with_consensus_parallax_colors_by_distance(self):
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

        result = generate_starmap(self.project)

        self.assertTrue(result.colored_by_distance)
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

    def test_empty_project_clears_starmaps(self):
        self._create_star()
        generate_starmap(self.project)
        self.assertTrue(self.project.preview_starmap)

        Star.objects.filter(project=self.project).delete()
        result = generate_starmap(self.project)

        self.project.refresh_from_db()
        self.assertEqual(result.n_stars, 0)
        self.assertFalse(self.project.preview_starmap)

    def test_regenerate_replaces_legacy_static_path(self):
        self._create_star()
        self.project.preview_starmap.name = 'static/images/project_previews/legacy_preview.png'
        self.project.full_starmap.name = 'static/images/project_previews/legacy_full.png'
        self.project.save(update_fields=['preview_starmap', 'full_starmap'])

        result = generate_starmap(self.project)

        self.project.refresh_from_db()
        self.assertTrue(result.preview_url)
        self.assertTrue(self.project.preview_starmap.name.startswith('projects/'))
        self.assertTrue(self.project.full_starmap.name.startswith('projects/'))


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
        self.editor = User.objects.create_user(username='editor', password='testpass123')
        self.viewer = User.objects.create_user(username='viewer', password='testpass123')
        self.project.readwrite_users.add(self.editor)
        self.project.readonly_users.add(self.viewer)

    def test_get_starmap_public(self):
        response = self.client.get(f'/api/dash/{self.project.slug}/starmap/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('preview_url', response.data)
        self.assertFalse(response.data['can_edit'])

    def test_get_starmap_private_forbidden_for_anonymous(self):
        self.project.is_public = False
        self.project.save(update_fields=['is_public'])
        response = self.client.get(f'/api/dash/{self.project.slug}/starmap/')
        self.assertEqual(response.status_code, 403)

    def test_regenerate_requires_edit_permission(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(f'/api/dash/{self.project.slug}/starmap/regenerate/')
        self.assertEqual(response.status_code, 403)

    def test_regenerate_allowed_for_editor(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(f'/api/dash/{self.project.slug}/starmap/regenerate/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['preview_url'])
        self.assertTrue(response.data['can_edit'])

    def test_dashboard_bootstrap_omits_starmap(self):
        response = self.client.get(f'/api/dash/{self.project.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('starmap', response.data)


class StarmapSchedulingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.project = Project.objects.create(name='Schedule', slug='schedule', description='')

    @patch('stars.tasks.regenerate_starmap_task.apply_async')
    def test_schedule_starmap_regeneration_is_debounced(self, mock_apply):
        self.assertTrue(schedule_starmap_regeneration(self.project.pk))
        self.assertFalse(schedule_starmap_regeneration(self.project.pk))
        mock_apply.assert_called_once()

    @patch('stars.tasks.schedule_starmap_regeneration')
    @patch('stars.tasks.import_gaia_dr3_for_star')
    def test_gaia_bulk_schedules_starmap_regeneration(self, mock_import, mock_schedule):
        from stars.services.gaia_import import GaiaImportResult

        star = Star.objects.create(name='G1', project=self.project, ra=1.0, dec=1.0)
        mock_import.return_value = GaiaImportResult(status='ok', message='ok', fields_updated=[])

        with patch.object(fetch_gaia_bulk_task, 'update_state'):
            fetch_gaia_bulk_task.run(self.project.pk, [star.pk], None)

        mock_schedule.assert_called_once_with(self.project.pk)


class RegenerateAllStarmapsTests(TestCase):
    def setUp(self):
        self.project_ok = Project.objects.create(name='Ok', slug='ok-proj', description='')
        self.project_fail = Project.objects.create(name='Fail', slug='fail-proj', description='')
        Star.objects.create(name='A', project=self.project_ok, ra=1.0, dec=1.0)
        Star.objects.create(name='B', project=self.project_fail, ra=2.0, dec=2.0)

    @patch('stars.services.starmap.generate_starmap')
    def test_regenerate_all_continues_after_failure(self, mock_generate):
        def side_effect(project, *, user=None):
            del user
            if project.slug == 'fail-proj':
                raise RuntimeError('plot failed')
            from stars.services.starmap import StarmapResult
            return StarmapResult(
                preview_url='/media/x.png',
                full_url='/media/y.png',
                generated_at='2020-01-01T00:00:00+00:00',
                n_stars=1,
                colored_by_distance=False,
            )

        mock_generate.side_effect = side_effect

        summary = regenerate_all_starmaps()

        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['ok'], 1)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(len(summary['errors']), 1)

    @patch('stars.tasks.regenerate_all_starmaps')
    def test_regenerate_all_starmaps_task_delegates(self, mock_regenerate):
        mock_regenerate.return_value = {'total': 0, 'ok': 0, 'failed': 0, 'errors': []}
        result = regenerate_all_starmaps_task()
        mock_regenerate.assert_called_once_with()
        self.assertEqual(result['ok'], 0)
