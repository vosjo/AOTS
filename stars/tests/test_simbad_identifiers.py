from unittest.mock import patch

from astropy.table import Table
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from stars.models import Identifier, Project
from stars.services import star_io
from stars.services.simbad_identifiers import sync_simbad_identifiers


def _mock_objectids_table(*names):
    return Table({'id': list(names)})


class SimbadIdentifiersServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='SimbadIds', description='')
        self.star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )

    @patch('stars.services.simbad_identifiers.Simbad.query_objectids')
    def test_sync_adds_new_identifiers(self, mock_query):
        mock_query.return_value = _mock_objectids_table(
            'Vega',
            'HIP 91262',
            'alf Lyr',
        )

        result = sync_simbad_identifiers(self.star)

        self.assertEqual(result.status, 'ok')
        self.assertEqual(result.added, 2)
        self.assertEqual(result.skipped, 1)
        names = set(self.star.identifier_set.values_list('name', flat=True))
        self.assertEqual(names, {'Vega', 'HIP 91262', 'alf Lyr'})
        hip = Identifier.objects.get(star=self.star, name='HIP 91262')
        self.assertIn('sim-id?Ident=HIP91262', hip.href)

    @patch('stars.services.simbad_identifiers.Simbad.query_objectids')
    def test_sync_not_found(self, mock_query):
        mock_query.return_value = None
        with patch('stars.services.simbad_identifiers.query_simbad_object', return_value=None):
            result = sync_simbad_identifiers(self.star)
        self.assertEqual(result.status, 'not_found')


class SimbadIdentifiersApiTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='SimbadApi', description='')
        self.star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )
        User = get_user_model()
        self.user = User.objects.create_user(username='simbaduser', password='pass')
        self.project.readwrite_users.add(self.user)
        self.client = APIClient()

    @patch('stars.services.simbad_identifiers.Simbad.query_objectids')
    def test_sync_requires_auth(self, mock_query):
        mock_query.return_value = _mock_objectids_table('Vega', 'HIP 91262')
        response = self.client.post(
            f'/api/systems/stars/{self.star.pk}/simbad/identifiers/',
        )
        self.assertEqual(response.status_code, 403)

    @patch('stars.services.simbad_identifiers.Simbad.query_objectids')
    def test_sync_success(self, mock_query):
        mock_query.return_value = _mock_objectids_table('Vega', 'HIP 91262')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/systems/stars/{self.star.pk}/simbad/identifiers/',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['added'], 1)
