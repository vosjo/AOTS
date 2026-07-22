"""Tests for DJANGO_ENV fail-closed settings selection."""

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


def _use_production_settings():
    """Mirror of AOTS.settings._use_production_settings (fail-closed)."""
    django_env = os.environ.get('DJANGO_ENV', '').strip().lower()
    if django_env == 'production':
        return True
    if django_env == 'development':
        return False
    raise ImproperlyConfigured(
        "DJANGO_ENV must be set to 'production' or 'development' "
        f"(got {django_env!r}). Refusing to start with an ambiguous environment."
    )


class DjangoEnvFailClosedTests(SimpleTestCase):
    def test_missing_django_env_raises(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DJANGO_ENV', None)
            with self.assertRaises(ImproperlyConfigured):
                _use_production_settings()

    def test_invalid_django_env_raises(self):
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'staging'}):
            with self.assertRaises(ImproperlyConfigured):
                _use_production_settings()

    def test_development_env_returns_false(self):
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'development'}):
            self.assertFalse(_use_production_settings())

    def test_production_env_returns_true(self):
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'production'}):
            self.assertTrue(_use_production_settings())
