from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from stars.models import Project, Star

User = get_user_model()


class DatatablesContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name='ContractProject',
            slug='contract-project',
            is_public=True,
        )
        Star.objects.create(
            name='ContractStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )

    def test_stars_list_keys(self):
        response = self.client.get(
            '/api/systems/stars/?format=datatables'
            '&keep=nphot,nspec,nlc,ra_hms,dec_dms,observing_status_display',
        )
        self.assertEqual(response.status_code, 200)
        row = response.data['data'][0]
        for key in (
            'name', 'ra', 'dec', 'nphot', 'nspec', 'nlc',
            'ra_hms', 'dec_dms', 'observing_status_display',
        ):
            self.assertIn(key, row)
