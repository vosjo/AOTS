from django.test import TestCase, override_settings

from dash.starmap_cache import (
    get_cached_starmap_embed,
    invalidate_starmap_cache,
    set_cached_starmap_embed,
)
from stars.models import Project, Star


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    },
)
class StarmapCacheTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.project = Project.objects.create(name='CacheProj', slug='cache-proj', description='')

    def test_set_and_get_cached_payload(self):
        payload = {'interactive': {'item': {'type': 'object'}}, 'n_stars': 3}
        set_cached_starmap_embed(self.project, 'light', payload)
        self.assertEqual(get_cached_starmap_embed(self.project, 'light'), payload)

    def test_invalidate_bumps_version_and_clears_embed(self):
        set_cached_starmap_embed(self.project, 'dark', {'interactive': {'item': {}}})
        version = invalidate_starmap_cache(self.project)
        self.project.refresh_from_db()
        self.assertEqual(self.project.starmap_cache_version, version)
        self.assertIsNone(get_cached_starmap_embed(self.project, 'dark'))

    def test_star_coordinate_change_invalidates_cache(self):
        set_cached_starmap_embed(self.project, 'light', {'interactive': {'item': {}}})
        star = Star.objects.create(name='S1', project=self.project, ra=10.0, dec=10.0)
        version_before = self.project.starmap_cache_version
        star.ra = 11.0
        star.save(update_fields=['ra'])
        self.project.refresh_from_db()
        self.assertGreater(self.project.starmap_cache_version, version_before)
        self.assertIsNone(get_cached_starmap_embed(self.project, 'light'))
