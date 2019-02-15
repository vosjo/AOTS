
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['a15.astro.physik.uni-potsdam.de', '141.89.178.17', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aotsdb',
        'USER': 'aotsuser',
        'PASSWORD': 'pgrts2018',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Logging
# https://docs.djangoproject.com/en/dev/topics/logging/#configuring-logging
# https://stackoverflow.com/questions/21943962/how-to-see-details-of-django-errors-with-gunicorn

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/aots/www/aots/AOTS/debug.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
            'formatter': 'standard'
        },
    },
    'loggers': {
       'gunicorn.errors': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': True,
        },
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'stars': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    },
}
