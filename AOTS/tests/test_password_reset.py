from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class PasswordResetApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='old-password-123',
        )

    def _csrf(self):
        return self.client.get('/api/auth/csrf/').json()['csrfToken']

    def test_request_sends_reset_email(self):
        csrf = self._csrf()
        response = self.client.post(
            '/api/auth/password-reset/',
            {'email': 'reset@example.com'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/accounts/reset/', mail.outbox[0].body)

    def test_request_unknown_email_still_succeeds(self):
        csrf = self._csrf()
        response = self.client.post(
            '/api/auth/password-reset/',
            {'email': 'nobody@example.com'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_validate_and_confirm_reset(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        csrf = self._csrf()

        validate = self.client.get(
            f'/api/auth/password-reset/validate/?uid={uid}&token={token}',
        )
        self.assertEqual(validate.status_code, 200)
        self.assertTrue(validate.json()['valid'])
        self.assertNotIn('username', validate.json())

        confirm = self.client.post(
            '/api/auth/password-reset/confirm/',
            {
                'uid': uid,
                'token': token,
                'new_password1': 'new-secure-password-99',
                'new_password2': 'new-secure-password-99',
            },
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(confirm.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-secure-password-99'))

    def test_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        csrf = self._csrf()
        response = self.client.post(
            '/api/auth/password-reset/confirm/',
            {
                'uid': uid,
                'token': 'invalid-token',
                'new_password1': 'new-secure-password-99',
                'new_password2': 'new-secure-password-99',
            },
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 400)


class PasswordResetSpaUrlTests(TestCase):
    def test_password_reset_routes_serve_spa_shell(self):
        for path in (
            '/accounts/password_reset/',
            '/accounts/password_reset/done/',
            '/accounts/reset/done/',
            '/accounts/password_change/done/',
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="app"')

    def test_reset_confirm_route_serves_spa_shell(self):
        response = self.client.get('/accounts/reset/abc/def/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app"')
