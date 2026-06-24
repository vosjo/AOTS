from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from stars.models import Identifier, Project, Star
from stars.services import star_io


class StarNameFilterTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='NameFilter', description='', is_public=True)
        self.star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )
        Identifier.objects.create(
            star=self.star,
            project=self.project,
            name='HIP 91262',
        )
        self.other = star_io.create_star(
            name='Betelgeuse',
            project=self.project,
            ra=88.79,
            dec=7.41,
        )
        self.client = APIClient()

    def test_filter_by_star_name(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&name=Vega',
        )
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pk'], self.star.pk)
        self.assertEqual(results[0]['name_match_basis'], 'name')
        self.assertIsNone(results[0]['matched_alias'])

    def test_filter_by_alias(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&name=91262',
        )
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['pk'], self.star.pk)
        self.assertEqual(results[0]['name_match_basis'], 'alias')
        self.assertEqual(results[0]['matched_alias'], 'HIP 91262')

    def test_no_match_metadata_without_name_filter(self):
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}',
        )
        self.assertEqual(response.status_code, 200)
        row = response.data['results'][0]
        self.assertIsNone(row['name_match_basis'])
        self.assertIsNone(row['matched_alias'])

    def test_name_match_preferred_when_both_match(self):
        Identifier.objects.create(
            star=self.star,
            project=self.project,
            name='Vega B',
        )
        response = self.client.get(
            f'/api/systems/stars/?project={self.project.pk}&name=Vega',
        )
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name_match_basis'], 'name')
