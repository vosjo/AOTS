from unittest.mock import patch

from astropy.table import Table
import numpy as np
from django.test import TestCase
from rest_framework.test import APIClient

from analysis.models import Parameter, ParameterSource
from analysis.services.consensus_defaults import seed_project_consensus_policies
from analysis.services.parameter_consensus import get_consensus_parameter
from observations.models import Photometry
from stars.models import Project, Star
from stars.services.gaia_import import (
    derive_absolute_g_mag,
    derive_bp_rp,
    derive_catalog_parameters,
    import_gaia_dr3_for_star,
)


def _mock_gaia_vizier_result(**overrides):
    defaults = {
        'Plx': 5.0,
        'e_Plx': 0.05,
        'pmRA': 100.0,
        'e_pmRA': 0.1,
        'pmDE': -50.0,
        'e_pmDE': 0.1,
        'Gmag': 10.0,
        'e_Gmag': 0.02,
        'BPmag': 10.5,
        'e_BPmag': 0.03,
        'RPmag': 9.5,
        'e_RPmag': 0.03,
    }
    defaults.update(overrides)
    return [Table([defaults])]


class GaiaDerivationTests(TestCase):
    def test_derive_bp_rp(self):
        value, error = derive_bp_rp(10.5, 0.03, 9.5, 0.04)
        self.assertAlmostEqual(value, 1.0)
        self.assertAlmostEqual(error, np.sqrt(0.03 ** 2 + 0.04 ** 2))

    def test_derive_absolute_g_mag(self):
        result = derive_absolute_g_mag(10.0, 0.02, 5.0, 0.05)
        self.assertIsNotNone(result)
        value, error = result
        expected = 10.0 + 5.0 * np.log10(5.0) - 10.0
        self.assertAlmostEqual(value, expected)
        self.assertGreater(error, 0)

    def test_derive_absolute_g_mag_skips_bad_parallax(self):
        self.assertIsNone(derive_absolute_g_mag(10.0, 0.02, -1.0, 0.05))
        self.assertIsNone(derive_absolute_g_mag(10.0, 0.02, 5.0, 0.2))

    def test_derive_catalog_parameters(self):
        derived = derive_catalog_parameters(
            gmag=10.0,
            gmag_err=0.02,
            bpmag=10.5,
            bpmag_err=0.03,
            rpmag=9.5,
            rpmag_err=0.03,
            parallax_mas=5.0,
            parallax_err_mas=0.05,
        )
        self.assertIn('mag', derived)
        self.assertIn('bp_rp', derived)
        self.assertIn('absolute_g_mag', derived)


class GaiaImportServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='GaiaTest', description='')
        seed_project_consensus_policies(self.project)
        self.star = Star.objects.create(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )

    @patch('stars.services.gaia_import._query_gaia_dr3')
    def test_import_stores_photometry_and_parameters(self, mock_query):
        mock_query.return_value = _mock_gaia_vizier_result()

        result = import_gaia_dr3_for_star(self.star)

        self.assertEqual(result.status, 'ok')
        self.assertIn('parallax', result.fields_updated)
        self.assertIn('mag', result.fields_updated)
        self.assertIn('bp_rp', result.fields_updated)
        self.assertIn('absolute_g_mag', result.fields_updated)
        self.assertEqual(
            Photometry.objects.filter(star=self.star, band='GAIA3.G').count(),
            1,
        )
        self.assertTrue(
            Parameter.objects.filter(
                star=self.star,
                name='parallax',
                parameter_source__name='Gaia DR3',
            ).exists(),
        )
        consensus = get_consensus_parameter(self.star, 'absolute_g_mag', 0)
        self.assertIsNotNone(consensus)

    @patch('stars.services.gaia_import._query_gaia_dr3')
    def test_import_no_match(self, mock_query):
        mock_query.return_value = None

        result = import_gaia_dr3_for_star(self.star)

        self.assertEqual(result.status, 'no_match')
        self.assertEqual(Photometry.objects.filter(star=self.star).count(), 0)

    @patch('stars.services.gaia_import._query_gaia_dr3')
    def test_import_replaces_existing_gaia_dr3(self, mock_query):
        source = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        from analysis.services import parameter_io

        parameter_io.create_measurement(
            star=self.star,
            parameter_source=source,
            name='parallax',
            value=1.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
        )
        self.star.photometry_set.create(
            band='GAIA3.G',
            measurement=99.0,
            error=0.1,
            unit='mag',
        )

        mock_query.return_value = _mock_gaia_vizier_result(Plx=5.0)

        import_gaia_dr3_for_star(self.star)

        parallax = Parameter.objects.get(
            star=self.star,
            name='parallax',
            parameter_source=source,
        )
        self.assertAlmostEqual(parallax.value, 5.0)
        gmag = Photometry.objects.get(star=self.star, band='GAIA3.G')
        self.assertAlmostEqual(gmag.measurement, 10.0)


class GaiaImportApiTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='GaiaApi', description='')
        self.star = Star.objects.create(
            name='Test',
            project=self.project,
            ra=10.0,
            dec=20.0,
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(username='gaiauser', password='pass')
        self.project.readwrite_users.add(self.user)
        self.client = APIClient()

    @patch('stars.services.gaia_import._query_gaia_dr3')
    def test_fetch_gaia_requires_auth(self, mock_query):
        mock_query.return_value = _mock_gaia_vizier_result()
        response = self.client.post(f'/api/systems/stars/{self.star.pk}/gaia/fetch/')
        self.assertEqual(response.status_code, 403)

    @patch('stars.services.gaia_import._query_gaia_dr3')
    def test_fetch_gaia_success(self, mock_query):
        mock_query.return_value = _mock_gaia_vizier_result()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/systems/stars/{self.star.pk}/gaia/fetch/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
