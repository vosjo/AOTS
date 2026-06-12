from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from observations.models import Observatory, Spectrum
from stars.models import Project, Star, Tag

User = get_user_model()

LIST_ENDPOINTS = [
    ('/api/systems/stars/', ('name', 'ra', 'dec', 'nphot', 'nspec', 'nlc')),
    ('/api/systems/tags/', ('name', 'color', 'pk')),
    ('/api/observations/spectra/', ('pk', 'hjd', 'instrument', 'has_raw_files')),
    ('/api/observations/specfiles/', ('pk', 'hjd', 'instrument')),
    ('/api/observations/rawspecfiles/', ('pk', 'instrument')),
    ('/api/observations/lightcurves/', ('pk', 'hjd', 'instrument')),
    ('/api/observations/observatories/', ('pk', 'name')),
    ('/api/analysis/analyses/', ('pk', 'name', 'category', 'category_label')),
]


class RestListContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name='ContractProject',
            slug='contract-project',
            is_public=True,
        )
        self.star = Star.objects.create(
            name='ContractStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )
        Tag.objects.create(name='t1', project=self.project, color='#fff')
        Spectrum.objects.create(
            project=self.project,
            star=self.star,
            hjd=2450000.0,
            instrument='TEST',
        )
        Observatory.objects.create(project=self.project, name='Obs1', short_name='O1')

    def test_rest_pagination_shape(self):
        for url, _keys in LIST_ENDPOINTS:
            with self.subTest(url=url):
                response = self.client.get(f'{url}?project={self.project.pk}')
                self.assertEqual(response.status_code, 200)
                self.assertIn('count', response.data)
                self.assertIn('results', response.data)
                self.assertIsInstance(response.data['results'], list)

    def test_stars_list_keys(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}',
        )
        row = response.data['results'][0]
        for key in ('name', 'ra', 'dec', 'nphot', 'nspec', 'nlc'):
            self.assertIn(key, row)

    def test_datatables_still_works(self):
        response = self.client.get(
            f'/api/systems/stars/?format=datatables&project={self.project.pk}',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)

    def test_ordering_param(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&ordering=-name',
        )
        self.assertEqual(response.status_code, 200)

    def test_page_size_param(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&page_size=5',
        )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.data['results']), 5)
