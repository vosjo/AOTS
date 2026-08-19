from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from observations.models import LightCurve
from stars.models import Project, Star

User = get_user_model()


def _minimal_tess_lc_bytes():
    import io

    import numpy as np
    from astropy.io import fits

    buf = io.BytesIO()
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
        'RA_OBJ': 10.0,
        'DEC_OBJ': 20.0,
        'OBJECT': 'UploadStar',
        'CREATOR': 'Lightkurve',
    }.items():
        primary.header[key] = value
        hdu.header[key] = value
    fits.HDUList([primary, hdu]).writeto(buf, overwrite=True)
    return buf.getvalue()


class BulkApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name='BulkProject',
            slug='bulk-project',
            is_public=False,
        )
        self.user = User.objects.create_user(username='bulkuser', password='testpass123')
        self.project.readwrite_users.add(self.user)
        self.star = Star.objects.create(
            name='BulkStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )
        self.api_user = User.objects.create_user(
            username='apiuser',
            password='testpass123',
            api_key='public-test-key',
            api_secret=make_password('secret-test-key'),
        )
        self.project.readwrite_users.add(self.api_user)

    def test_bulk_download_start_requires_star_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/',
            HTTP_PROJECTID=str(self.project.pk),
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_download_start_rejects_invalid_kind(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/?kind=invalid',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST=str(self.star.pk),
        )
        self.assertEqual(response.status_code, 400)

    @patch('observations.api.bulk.run_task', return_value=(None, 'test-task-id'))
    def test_bulk_download_start_accepts_lightcurves_kind(self, mock_run_task):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/?kind=lightcurves',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST='1',
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['kind'], 'lightcurves')

    @patch('observations.api.bulk.run_task', return_value=(None, 'test-task-id'))
    def test_bulk_download_start_accepts_analyses_kind(self, mock_run_task):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/?kind=analyses',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST='1',
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['kind'], 'analyses')

    @patch('observations.api.bulk.run_task', return_value=(None, 'test-task-id'))
    def test_bulk_download_start_accepts_raw_kind(self, mock_run_task):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/?kind=raw',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST='999',
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['kind'], 'raw')
        mock_run_task.assert_called_once()

    def test_bulk_download_start_requires_auth(self):
        response = self.client.post(
            '/api/observations/bulk-download/start/',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST=str(self.star.pk),
        )
        self.assertEqual(response.status_code, 403)

    def test_task_status_forbidden_for_other_user(self):
        from AOTS.task_metadata import store_task_owner

        task_id = '11111111-1111-4111-8111-111111111111'
        store_task_owner(task_id, self.api_user.pk)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/observations/tasks/{task_id}/')
        self.assertEqual(response.status_code, 403)

    def test_api_key_auth_on_bulk_upload_missing_project(self):
        response = self.client.post(
            '/api/observations/api-spec-upload/',
            HTTP_PUBLICAPIKEY='public-test-key',
            HTTP_SECRETAPIKEY='secret-test-key',
        )
        self.assertEqual(response.status_code, 400)

    def test_lc_upload_readwriteown_user(self):
        own_user = User.objects.create_user(username='lcown', password='testpass123')
        self.project.readwriteown_users.add(own_user)
        self.client.force_authenticate(user=own_user)
        content = _minimal_tess_lc_bytes()
        response = self.client.post(
            '/api/observations/api-lc-upload/',
            {
                'project': str(self.project.pk),
                'lcfile': SimpleUploadedFile('sector1_lc.fits', content),
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('New light curve', response.data['detail'])
        lc = LightCurve.objects.get()
        self.assertTrue(lc.lcfile)
        self.assertEqual(lc.project_id, self.project.pk)

    def test_lc_upload_duplicate_returns_clear_message(self):
        content = _minimal_tess_lc_bytes()
        self.client.force_authenticate(user=self.user)
        first = self.client.post(
            '/api/observations/api-lc-upload/',
            {
                'project': str(self.project.pk),
                'lcfile': SimpleUploadedFile('a.fits', content),
            },
            format='multipart',
        )
        self.assertEqual(first.status_code, 200)
        second = self.client.post(
            '/api/observations/api-lc-upload/',
            {
                'project': str(self.project.pk),
                'lcfile': SimpleUploadedFile('b.fits', content),
            },
            format='multipart',
        )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(
            second.data['detail'],
            'This light curve is a duplicate and was not added!',
        )
        self.assertEqual(LightCurve.objects.count(), 1)
