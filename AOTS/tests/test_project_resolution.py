from django.contrib.auth import get_user_model
from django.test import TestCase

from AOTS.project_resolution import get_object_project
from analysis.models import Parameter
from stars.models import Project, Star

User = get_user_model()


class ProjectResolutionTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='ResolveProject',
            slug='resolve-project',
            is_public=True,
        )
        self.star = Star.objects.create(
            name='ResolveStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )
        self.parameter = Parameter.objects.create(
            star=self.star,
            name='Teff',
            component=1,
            value=5000,
            error=100,
            unit='K',
        )

    def test_project_resolves_to_self(self):
        self.assertEqual(get_object_project(self.project), self.project)

    def test_parameter_resolves_via_star(self):
        self.assertEqual(get_object_project(self.parameter), self.project)
