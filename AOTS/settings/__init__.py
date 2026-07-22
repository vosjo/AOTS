"""
Django settings entry point.

Select environment via DJANGO_ENV=development|production.
Unset or unknown values fail closed (ImproperlyConfigured).
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403


def _use_production_settings():
    django_env = os.environ.get('DJANGO_ENV', '').strip().lower()
    if django_env == 'production':
        return True
    if django_env == 'development':
        return False
    raise ImproperlyConfigured(
        "DJANGO_ENV must be set to 'production' or 'development' "
        f"(got {django_env!r}). Refusing to start with an ambiguous environment."
    )


if _use_production_settings():
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
