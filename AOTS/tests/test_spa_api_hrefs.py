from importlib import reload

from django.test import TestCase, override_settings
from django.urls import clear_url_caches

from stars.models import Project, Star


def _reload_urlconf():
    import AOTS.urls as urls_module

    reload(urls_module)
    clear_url_caches()


@override_settings(AOTS_SPA_CUTOVER=True, VITE_DEV=False)
class SpaCutoverApiHrefTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _reload_urlconf()

    @classmethod
    def tearDownClass(cls):
        with override_settings(AOTS_SPA_CUTOVER=False):
            _reload_urlconf()
        super().tearDownClass()

    def setUp(self):
        self.project = Project.objects.create(
            name='HrefProject',
            slug='href-project',
            is_public=True,
        )
        self.star = Star.objects.create(
            name='HrefStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )

    def test_star_list_api_returns_spa_href(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&page=1&page_size=20'
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]['href'],
            f'/w/{self.project.slug}/systems/stars/{self.star.pk}',
        )
