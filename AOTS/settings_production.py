
import os

import environ

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env("DATABASE_HOST"),
        'PORT': env("DATABASE_PORT"),
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
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': env("LOG_FILE"),
#             'maxBytes': 1024 * 1024 * 100,  # 100 mb
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
#             'level': 'INFO',
            'level': 'DEBUG',
            'propagate': True,
        },
        'stars': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    },
}
