from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from AOTS.api_auth import LoginRateThrottle


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    },
)
class AuthLoginThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        User.objects.create_user(username='throttleuser', password='secret-pass')
        self.client = Client(enforce_csrf_checks=True)
        self._original_rate = LoginRateThrottle.rate
        LoginRateThrottle.rate = '3/min'

    def tearDown(self):
        LoginRateThrottle.rate = self._original_rate
        cache.clear()

    def _login(self):
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        return self.client.post(
            '/api/auth/login/',
            {'username': 'throttleuser', 'password': 'wrong-password'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )

    def test_repeated_failed_logins_are_throttled(self):
        for _ in range(3):
            response = self._login()
            self.assertEqual(response.status_code, 400)
        throttled = self._login()
        self.assertEqual(throttled.status_code, 429)
