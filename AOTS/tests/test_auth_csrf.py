from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class AuthCsrfTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='csrfuser', password='secret-pass')
        self.client = Client(enforce_csrf_checks=True)

    def test_login_returns_fresh_csrf_token(self):
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'csrfuser', 'password': 'secret-pass'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['authenticated'])
        self.assertIn('csrfToken', response.json())
        self.assertNotEqual(response.json()['csrfToken'], '')

    def test_post_after_login_uses_login_csrf_token(self):
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        login = self.client.post(
            '/api/auth/login/',
            {'username': 'csrfuser', 'password': 'secret-pass'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(login.status_code, 200)
        new_csrf = login.json()['csrfToken']

        response = self.client.post(
            '/api/auth/logout/',
            {},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=new_csrf,
        )
        self.assertEqual(response.status_code, 200)
