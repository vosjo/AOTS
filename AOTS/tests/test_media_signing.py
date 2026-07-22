"""Tests for signed media download URLs."""

import os
import time
from pathlib import Path

from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from AOTS.media_signing import sign_media_payload, signed_media_url
from observations.models import SpecFile
from stars.models import Project


@override_settings(MEDIA_USE_X_ACCEL=True, MEDIA_SIGNED_URL_MAX_AGE=60)
class SignedMediaDownloadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(name='MediaProj', description='', is_public=True)
        self.spec = SpecFile(project=self.project, original_name='star.fits')
        self.spec.specfile.save('star.fits', ContentFile(b'SIMPLE  =                    T'), save=True)

    def test_signed_url_returns_x_accel_headers(self):
        url = signed_media_url(self.spec.specfile.name, original_name=self.spec.original_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Accel-Redirect', response)
        self.assertTrue(response['X-Accel-Redirect'].startswith('/protected-media/'))
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('star.fits', response['Content-Disposition'])

    def test_tampered_token_rejected(self):
        token = sign_media_payload(self.spec.specfile.name, original_name='star.fits')
        response = self.client.get(reverse('api-media-download', kwargs={'token': token + 'x'}))
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_SIGNED_URL_MAX_AGE=1)
    def test_expired_token_returns_410(self):
        token = sign_media_payload(self.spec.specfile.name, original_name='star.fits')
        time.sleep(1.1)
        response = self.client.get(reverse('api-media-download', kwargs={'token': token}))
        self.assertEqual(response.status_code, 410)

    def test_path_traversal_in_token_rejected(self):
        from django.core import signing
        from AOTS.media_signing import MEDIA_SIGNING_SALT

        token = signing.dumps({'p': '../etc/passwd', 'n': 'x'}, salt=MEDIA_SIGNING_SALT)
        response = self.client.get(reverse('api-media-download', kwargs={'token': token}))
        self.assertIn(response.status_code, (403, 404))

    @override_settings(MEDIA_USE_X_ACCEL=False)
    def test_dev_mode_streams_file(self):
        url = signed_media_url(self.spec.specfile.name, original_name=self.spec.original_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'SIMPLE  =                    T')


class SpecFileDownloadUrlSerializerTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='SerProj', description='', is_public=True)
        self.spec = SpecFile(project=self.project, original_name='orig.fits')
        self.spec.specfile.save('orig.fits', ContentFile(b'SIMPLE  =                    T'), save=True)

    def test_serializer_returns_signed_api_url(self):
        from observations.api.serializers import SpectrumSpecFileDetailSerializer

        data = SpectrumSpecFileDetailSerializer(self.spec).data
        self.assertTrue(data['download_url'].startswith('/api/media/'))
        self.assertNotIn('/media/spectra/', data['download_url'])
