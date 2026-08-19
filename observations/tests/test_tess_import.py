from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from observations.models import LightCurve, Observatory
from observations.services.tess_import import (
    import_tess_lightcurves_for_star,
    query_tess_lc_products,
)
from stars.models import Project, Star


class TessImportServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='TessTest', description='')
        self.star = Star.objects.create(
            name='Target',
            project=self.project,
            ra=97.644,
            dec=29.674,
        )

    def test_import_requires_coordinates(self):
        star = Star.objects.create(name='NoCoords', project=self.project, ra=-1, dec=-1)
        result = import_tess_lightcurves_for_star(star)
        self.assertEqual(result.status, 'error')
        self.assertIn('coordinates', result.message.lower())

    @patch('observations.services.tess_import.Observations.download_products')
    @patch('observations.services.tess_import.query_tess_lc_products')
    def test_import_creates_lightcurves(self, mock_query, mock_download):
        mock_query.return_value = [{'productFilename': 'tess_sector1_lc.fits'}]
        mock_download.side_effect = lambda row, download_dir: {
            'Local Path': [self._write_fake_lc(download_dir, row['productFilename'])],
        }

        result = import_tess_lightcurves_for_star(self.star)
        self.assertEqual(result.status, 'ok')
        self.assertEqual(len(result.imported), 1)
        lc = LightCurve.objects.get(pk=result.imported[0])
        self.assertEqual(lc.star_id, self.star.pk)
        self.assertEqual(lc.telescope, 'TESS')
        self.assertEqual(lc.passband, 'TESS.RED')
        self.assertTrue(lc.observatory.space_craft)
        self.assertEqual(lc.observatory.name, 'TESS')
        self.assertEqual(lc.observatory.telescopes, 'TESS')

    @patch('observations.services.tess_import.Observations.download_products')
    @patch('observations.services.tess_import.query_tess_lc_products')
    def test_import_does_not_match_ground_observatory_at_null_island(self, mock_query, mock_download):
        ground = Observatory.objects.create(
            project=self.project,
            name='Default site',
            latitude=0,
            longitude=0,
            altitude=0,
            space_craft=False,
        )
        mock_query.return_value = [{'productFilename': 'tess_sector1_lc.fits'}]
        mock_download.side_effect = lambda row, download_dir: {
            'Local Path': [self._write_fake_lc(download_dir, row['productFilename'])],
        }

        result = import_tess_lightcurves_for_star(self.star)

        self.assertEqual(result.status, 'ok')
        lc = LightCurve.objects.get(pk=result.imported[0])
        self.assertNotEqual(lc.observatory_id, ground.pk)
        self.assertTrue(lc.observatory.space_craft)
        self.assertEqual(lc.observatory.name, 'TESS')

    @patch('observations.services.tess_import.Observations.download_products')
    @patch('observations.services.tess_import.query_tess_lc_products')
    def test_import_skips_duplicates(self, mock_query, mock_download):
        mock_query.return_value = [{'productFilename': 'tess_sector1_lc.fits'}]
        mock_download.side_effect = lambda row, download_dir: {
            'Local Path': [self._write_fake_lc(download_dir, row['productFilename'])],
        }

        first = import_tess_lightcurves_for_star(self.star)
        second = import_tess_lightcurves_for_star(self.star)

        self.assertEqual(first.status, 'ok')
        self.assertEqual(second.status, 'partial')
        self.assertEqual(second.skipped_duplicates, 1)
        self.assertEqual(LightCurve.objects.filter(star=self.star).count(), 1)

    @patch('observations.services.tess_import.Observations.get_product_list')
    @patch('observations.services.tess_import.Observations.query_criteria')
    def test_query_filters_lc_products(self, mock_query_criteria, mock_product_list):
        from astropy.table import Table

        mock_query_criteria.return_value = Table({
            'dataproduct_type': ['timeseries', 'image'],
            'obs_id': ['a', 'b'],
        })
        mock_product_list.return_value = Table({
            'productFilename': [
                'tess_a_lc.fits',
                'tess_a_tp.fits',
                'tess_a_lc.fits',
            ],
            'productSubGroupDescription': ['LC', 'TP', 'LC'],
            'productType': ['SCIENCE', 'SCIENCE', 'SCIENCE'],
        })

        products = query_tess_lc_products(self.star)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['productFilename'], 'tess_a_lc.fits')

    def _write_fake_lc(self, download_dir, filename):
        import numpy as np
        from astropy.io import fits

        path = f'{download_dir}/{filename}'
        cols = fits.ColDefs([
            fits.Column(name='TIME', format='D', array=np.array([100.0, 100.001])),
            fits.Column(name='PDCSAP_FLUX', format='E', array=np.array([1.0, 1.01], dtype='f4')),
        ])
        hdu = fits.BinTableHDU.from_columns(cols)
        primary = fits.PrimaryHDU()
        for key, value in {
            'TELESCOP': 'TESS',
            'INSTRUME': 'TESS Photometer',
            'TSTART': 100.0,
            'TSTOP': 200.0,
            'RA_OBJ': self.star.ra,
            'DEC_OBJ': self.star.dec,
            'OBJECT': self.star.name,
            'CREATOR': 'Lightkurve',
            'FILEVER': '1.0',
            'DATA_REL': '1',
        }.items():
            primary.header[key] = value
            hdu.header[key] = value
        fits.HDUList([primary, hdu]).writeto(path, overwrite=True)
        return path


class TessImportApiTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.project = Project.objects.create(name='TessApi', description='')
        self.star = Star.objects.create(
            name='Target',
            project=self.project,
            ra=97.644,
            dec=29.674,
        )
        self.user = User.objects.create_user(username='tessuser', password='pass')
        self.project.readwrite_users.add(self.user)
        self.client = APIClient()

    def test_fetch_requires_auth(self):
        response = self.client.post(f'/api/systems/stars/{self.star.pk}/tess/fetch/')
        self.assertEqual(response.status_code, 403)

    @patch('stars.api.tess_views.import_tess_lightcurves_for_star')
    def test_fetch_success(self, mock_import):
        from observations.services.tess_import import TessImportResult

        mock_import.return_value = TessImportResult(
            status='ok',
            message='Imported 2 TESS light curve(s).',
            imported=[1, 2],
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/systems/stars/{self.star.pk}/tess/fetch/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['imported'], [1, 2])


class TessBulkImportApiTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.project = Project.objects.create(name='TessBulkApi', description='')
        self.star = Star.objects.create(
            name='Target',
            project=self.project,
            ra=97.644,
            dec=29.674,
        )
        self.user = User.objects.create_user(username='tessbulkuser', password='pass')
        self.project.readwrite_users.add(self.user)
        self.client = APIClient()

    @patch('stars.api.tess_views.import_tess_lightcurves_for_star')
    def test_bulk_fetch_selected(self, mock_import):
        from observations.services.tess_import import TessImportResult

        mock_import.return_value = TessImportResult(
            status='ok',
            message='Imported 1 TESS light curve(s).',
            imported=[10],
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/systems/stars/tess/fetch-bulk/',
            {'star_ids': [self.star.pk]},
            format='json',
            HTTP_PROJECTID=str(self.project.pk),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['ok'], 1)
        self.assertEqual(body['imported_lightcurves'], 1)
