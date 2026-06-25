"""
Production settings for AOTS.
"""

from .base import CELERY_BROKER_URL, REST_FRAMEWORK as BASE_REST_FRAMEWORK, env

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT', default=''),
    }
}

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True

from .base import INSTALLED_APPS as BASE_INSTALLED_APPS
from .base import MIDDLEWARE as BASE_MIDDLEWARE, env

INSTALLED_APPS = [*BASE_INSTALLED_APPS, 'csp']

MIDDLEWARE = [
    BASE_MIDDLEWARE[0],
    'csp.middleware.CSPMiddleware',
    *BASE_MIDDLEWARE[1:],
]

from csp.constants import NONCE

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", NONCE, 'https://cdn.bokeh.org'),
        'style-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", 'data:', 'blob:', 'https:'),
        'media-src': ("'self'", 'data:', 'blob:'),
        'connect-src': ("'self'",),
        'font-src': ("'self'", 'data:'),
        'frame-ancestors': ("'self'",),
    },
}

# Shared cache for task ownership (Gunicorn workers) and optional TTL helpers
_cache_url = env('CACHE_URL', default='')
if not _cache_url and CELERY_BROKER_URL.startswith('redis://'):
    _cache_url = CELERY_BROKER_URL.rsplit('/', 1)[0] + '/1'

if _cache_url:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _cache_url,
        }
    }

REST_FRAMEWORK = {
    **BASE_REST_FRAMEWORK,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{name}] {levelname} {module}:{lineno} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'AOTS': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
