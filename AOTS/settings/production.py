"""
Production settings for AOTS.
"""

from .base import CELERY_BROKER_URL, REST_FRAMEWORK as BASE_REST_FRAMEWORK, env
from .base import SPECTACULAR_SETTINGS as BASE_SPECTACULAR_SETTINGS

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

# Local MTA (sendmail replacement) on localhost:25 by default.
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)

# Private media downloads use nginx X-Accel-Redirect in production.
MEDIA_USE_X_ACCEL = env.bool('MEDIA_USE_X_ACCEL', default=True)

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

# Aladin Lite (StarDetailView): HiPS tiles, VizieR proxy, WASM bootstrap.
_ALADIN_CONNECT_SRC = (
    'https://alasky.cds.unistra.fr',
    'https://alaskybis.cds.unistra.fr',
    'https://alasky.unistra.fr',
    'https://alaskybis.unistra.fr',
    'https://aladin.cds.unistra.fr',
    'https://cds.unistra.fr',
    'https://vizier.unistra.fr',
    'https://axel.cds.unistra.fr',
    'https://simbad.cds.unistra.fr',
    'https://dachs.ivoa.srcnet.skao.int',
)

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        # No inline scripts in spa/index.html; Bokeh uses json_item + CDN only.
        # Do not use 'strict-dynamic' here — it disables 'self' for parser-inserted scripts.
        'script-src': ("'self'", 'https://cdn.bokeh.org', "'wasm-unsafe-eval'"),
        # Vue and Bokeh inject inline styles; nonces would require broader SPA rework.
        'style-src': ("'self'", "'unsafe-inline'"),
        # Aladin HiPS tiles come from many survey hosts; keep https: wildcard for img.
        'img-src': ("'self'", 'data:', 'blob:', 'https:'),
        'media-src': ("'self'", 'data:', 'blob:'),
        'connect-src': ("'self'", 'data:', 'blob:', *_ALADIN_CONNECT_SRC),
        'worker-src': ("'self'", 'blob:'),
        'font-src': ("'self'", 'data:'),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
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
    ),
}

SPECTACULAR_SETTINGS = {
    **BASE_SPECTACULAR_SETTINGS,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
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
