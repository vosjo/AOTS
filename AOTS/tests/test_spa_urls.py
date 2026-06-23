from importlib import reload

from django.test import TestCase, override_settings
from django.urls import clear_url_caches
from django.urls import reverse


def _reload_urlconf():
    import AOTS.urls as urls_module

    reload(urls_module)
    clear_url_caches()


@override_settings(AOTS_SPA_CUTOVER=True, VITE_DEV=False)
class SpaCutoverUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _reload_urlconf()

    @classmethod
    def tearDownClass(cls):
        with override_settings(AOTS_SPA_CUTOVER=False):
            _reload_urlconf()
        super().tearDownClass()
    def test_root_redirects_to_projects(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/w/projects/', fetch_redirect_response=False)

    def test_projects_serves_spa_shell(self):
        response = self.client.get('/w/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')
        self.assertContains(response, "routerBase: '/'")
        self.assertNotContains(response, 'datatables')

    def test_nested_w_route_serves_spa_shell(self):
        response = self.client.get('/w/demo-project/systems/stars/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')

    def test_app_prefix_redirects_to_production_path(self):
        response = self.client.get('/app/w/projects/')
        self.assertRedirects(response, '/w/projects/', fetch_redirect_response=False)


@override_settings(AOTS_SPA_CUTOVER=False, VITE_DEV=False)
class LegacyUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _reload_urlconf()

    @classmethod
    def tearDownClass(cls):
        _reload_urlconf()
        super().tearDownClass()

    def test_projects_serves_legacy_template(self):
        response = self.client.get('/w/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'datatables')

    def test_app_prefix_serves_spa_shell(self):
        response = self.client.get('/app/w/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')
        self.assertContains(response, 'routerBase: \'/app/\'')

    def test_projects_url_name_still_resolves(self):
        self.assertEqual(reverse('projects'), '/w/projects/')
