"""
Django settings entry point.

Select environment via DJANGO_ENV=development|production.
Falls back to DEVICE hostname matching for backwards compatibility.
"""

import os
import platform

from .base import *  # noqa: F401,F403

from .base import env


def _use_production_settings():
    django_env = os.environ.get('DJANGO_ENV', '').lower()
    if django_env == 'production':
        return True
    if django_env == 'development':
        return False
    device = env('DEVICE', default='')
    return bool(device) and device in platform.node()


if _use_production_settings():
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
