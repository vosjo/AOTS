from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.categories import AnalysisCategory
from analysis.models import Analysis, DerivedParameter, Parameter, ParameterSource
from analysis.services.parameter_sources import get_or_create_avg_source
from stars.models import Project, Star

User = get_user_model()


class AnalysisApiTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='ApiProj', description='', is_public=True)
        self.star = Star.objects.create(name='S1', project=self.project, ra=1.0, dec=2.0)
        self.analysis = Analysis.objects.create(
            project=self.project,
            star=self.star,
            name='test analysis',
            datafile=SimpleUploadedFile('a.h5', b'x'),
        )
        self.client = APIClient()

    def test_analysis_list_includes_added_on_key(self):
        response = self.client.get(
            f'/api/analysis/analyses/?project={self.project.pk}&page=1&page_size=20',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertIn('added_on', response.data['results'][0])

    def test_parameter_list_includes_provenance(self):
        src = ParameterSource.objects.create(name='Gaia', project=self.project)
        Parameter.objects.create(
            star=self.star, name='teff', component=0, value=5000, error=100,
            unit='K', parameter_source=src,
        )
        response = self.client.get(
            f'/api/analysis/parameters/?project={self.project.pk}',
        )
        self.assertEqual(response.status_code, 200)
        row = next(r for r in response.data['results'] if r['name'] == 'teff')
        self.assertEqual(row['parameter_source']['name'], 'Gaia')
        self.assertIsNone(row['analysis'])

    def test_analysis_detail_includes_derived_parameters(self):
        self.analysis.category = AnalysisCategory.RV_SOLUTION
        self.analysis.save()
        avg = get_or_create_avg_source(self.project)
        src = ParameterSource.objects.create(name='src', project=self.project)
        for comp, val in ((1, 5.0), (2, 10.0)):
            Parameter.objects.create(
                star=self.star, name='K', component=comp, value=val, error=0.5,
                unit='km/s', average=True, parameter_source=avg,
            )
            Parameter.objects.create(
                star=self.star, name='K', component=comp, value=val, error=0.5,
                unit='km/s', average=False, parameter_source=src,
            )
        Parameter.objects.create(
            star=self.star, name='p', component=0, value=10.0, error=0.1,
            unit='d', average=True, parameter_source=avg,
        )
        Parameter.objects.create(
            star=self.star, name='e', component=0, value=0.0, error=0.01,
            unit='', average=True, parameter_source=avg,
        )
        dpar = DerivedParameter.objects.create(
            star=self.star, name='q', component=0, average=True, parameter_source=avg,
        )
        from analysis.services import parameter_derivation
        parameter_derivation.refresh_derived_parameter(dpar)

        response = self.client.get(f'/api/analysis/analyses/{self.analysis.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['has_derived_definitions'])
        self.assertEqual(len(response.data['derived_parameters']), 1)
        self.assertEqual(response.data['derived_parameters'][0]['name'], 'q')
        self.assertFalse(response.data['can_edit'])

    def test_derive_parameters_endpoint_requires_write_access(self):
        user = User.objects.create_user(username='rw', password='x')
        self.project.readwrite_users.add(user)
        self.analysis.category = AnalysisCategory.RV_SOLUTION
        self.analysis.save()
        avg = get_or_create_avg_source(self.project)
        Parameter.objects.create(
            star=self.star, name='K', component=1, value=5.0, error=0.5,
            unit='km/s', average=True, parameter_source=avg,
        )
        Parameter.objects.create(
            star=self.star, name='K', component=2, value=10.0, error=1.0,
            unit='km/s', average=True, parameter_source=avg,
        )
        Parameter.objects.create(
            star=self.star, name='p', component=0, value=10.0, error=0.1,
            unit='d', average=True, parameter_source=avg,
        )
        Parameter.objects.create(
            star=self.star, name='e', component=0, value=0.0, error=0.01,
            unit='', average=True, parameter_source=avg,
        )

        self.client.force_authenticate(user=user)
        response = self.client.post(
            f'/api/analysis/analyses/{self.analysis.pk}/derive-parameters/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['created'], 1)
        self.assertIn('derived_parameters', response.data)
        q = next(p for p in response.data['derived_parameters'] if p['name'] == 'q')
        self.assertAlmostEqual(q['rvalue'], 0.5, places=1)

    def test_derive_parameters_rejects_category_without_definitions(self):
        user = User.objects.create_user(username='rw2', password='x')
        self.project.readwrite_users.add(user)
        self.analysis.category = AnalysisCategory.SED_FIT
        self.analysis.save()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            f'/api/analysis/analyses/{self.analysis.pk}/derive-parameters/',
        )
        self.assertEqual(response.status_code, 400)
