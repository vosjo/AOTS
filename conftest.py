import os

import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')
os.environ.setdefault('DJANGO_ENV', 'development')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-pytest-only')
os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', 'True')

django.setup()


@pytest.fixture
def public_project(db):
    from stars.models import Project

    return Project.objects.create(
        name='PublicFixtureProject',
        slug='public-fixture',
        is_public=True,
    )


@pytest.fixture
def private_project(db):
    from stars.models import Project

    return Project.objects.create(
        name='PrivateFixtureProject',
        slug='private-fixture',
        is_public=False,
    )


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username='fixtureuser',
        password='testpass123',
    )
