from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.models import Analysis, Parameter, ParameterSource
from stars.models import Project, Star


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
