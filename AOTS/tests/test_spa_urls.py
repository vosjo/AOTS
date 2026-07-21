from django.test import TestCase, override_settings


@override_settings(VITE_DEV=False)
class SpaUrlTests(TestCase):
    def test_root_redirects_to_projects(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/w/projects/', fetch_redirect_response=False)

    def test_projects_serves_spa_shell(self):
        response = self.client.get('/w/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')
        self.assertContains(response, 'name="aots-router-base"')
        self.assertContains(response, 'content="/"')
        self.assertNotContains(response, 'datatables')
        self.assertContains(response, '/static/dist/assets/')
        self.assertContains(response, 'type="module"')

    def test_nested_w_route_serves_spa_shell(self):
        response = self.client.get('/w/demo-project/systems/stars/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')

    def test_users_route_serves_spa_shell(self):
        response = self.client.get('/users/you/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')

    def test_admin_route_serves_spa_shell(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')

    def test_app_prefix_redirects_to_production_path(self):
        response = self.client.get('/app/w/projects/')
        self.assertRedirects(response, '/w/projects/', fetch_redirect_response=False)

    def test_projects_url_name_still_resolves(self):
        from django.urls import reverse

        self.assertEqual(reverse('projects'), '/w/projects/')
