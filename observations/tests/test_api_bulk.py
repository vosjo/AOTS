from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework.test import APIClient

from stars.models import Project, Star

User = get_user_model()


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
    def test_bulk_download_start_accepts_datasets_kind(self, mock_run_task):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/observations/bulk-download/start/?kind=datasets',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST='1',
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['kind'], 'datasets')

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

        store_task_owner('fake-task-id', self.api_user.pk)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/observations/tasks/fake-task-id/')
        self.assertEqual(response.status_code, 403)

    def test_api_key_auth_on_bulk_upload_missing_project(self):
        response = self.client.post(
            '/api/observations/api-spec-upload/',
            HTTP_PUBLICAPIKEY='public-test-key',
            HTTP_SECRETAPIKEY='secret-test-key',
        )
        self.assertEqual(response.status_code, 400)
