from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.categories import AnalysisCategory
from analysis.models import Analysis, Parameter, ParameterSource
from analysis.services import parameter_io
from stars.models import Project, Star

User = get_user_model()


class ParameterIoApiTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='IoApi', description='', is_public=True)
        self.user = User.objects.create_user(username='rw', password='x')
        self.project.readwrite_users.add(self.user)
        self.star = Star.objects.create(name='S1', project=self.project, ra=1.0, dec=2.0)
        self.analysis = Analysis.objects.create(
            project=self.project, star=self.star, name='rv', category=AnalysisCategory.RV_CURVE,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_patch_valid_triggers_average_sync(self):
        ParameterSource.objects.create(name='src', project=self.project)
        p = parameter_io.create_measurement(
            star=self.star, name='teff', component=0, value=5000,
            error_l=100, error_u=100, unit='K', analysis=self.analysis, run_after=False,
        )
        parameter_io.after_star_parameters_batch(self.star)
        response = self.client.patch(
            f'/api/analysis/parameters/{p.pk}/',
            {'valid': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Parameter.objects.filter(star=self.star, name='teff', average=True, valid=True).exists(),
        )
