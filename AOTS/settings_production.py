
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
