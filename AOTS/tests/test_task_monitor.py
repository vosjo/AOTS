from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from AOTS.task_metadata import get_task_owner, list_task_ids, register_task
from AOTS.task_status import build_task_status_payload

User = get_user_model()


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    },
)
class TaskMetadataTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_register_task_indexes_and_stores_metadata(self):
        register_task(
            'task-abc',
            user_id=7,
            project_id=3,
            task_name='stars.tasks.fetch_tess_bulk_task',
            label='2 star(s)',
        )

        self.assertEqual(list_task_ids()[0], 'task-abc')
        meta = get_task_owner('task-abc')
        self.assertEqual(meta['user_id'], 7)
        self.assertEqual(meta['project_id'], 3)
        self.assertEqual(meta['task_name'], 'stars.tasks.fetch_tess_bulk_task')
        self.assertEqual(meta['label'], '2 star(s)')
        self.assertIn('created_at', meta)

    def test_register_task_moves_existing_id_to_front(self):
        register_task('older-task', user_id=1)
        register_task('newer-task', user_id=1)

        self.assertEqual(list_task_ids()[:2], ['newer-task', 'older-task'])


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    },
    CELERY_TASK_ALWAYS_EAGER=True,
)
class AdminTaskApiTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
        )
        self.user = User.objects.create_user(
            username='normal',
            password='testpass123',
        )
        register_task(
            'listed-task',
            user_id=self.superuser.pk,
            project_id=None,
            task_name='observations.tasks.build_bulk_download_zip_task',
            label='processed ZIP, 5 star(s)',
        )

    def test_anonymous_forbidden(self):
        response = self.client.get('/api/admin/tasks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/admin/tasks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('AOTS.task_status.AsyncResult')
    def test_superuser_lists_registered_tasks(self, mock_async_result):
        mock_async_result.return_value.status = 'SUCCESS'
        mock_async_result.return_value.ready.return_value = True
        mock_async_result.return_value.failed.return_value = False
        mock_async_result.return_value.successful.return_value = True
        mock_async_result.return_value.result = {'status': 'ready'}

        self.client.force_login(self.superuser)
        response = self.client.get('/api/admin/tasks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual(row['task_id'], 'listed-task')
        self.assertEqual(row['task_display'], 'Bulk download')
        self.assertEqual(row['label'], 'processed ZIP, 5 star(s)')
        self.assertEqual(row['username'], 'admin')

    @patch('AOTS.task_status.AsyncResult')
    def test_active_only_filter(self, mock_async_result):
        mock_async_result.return_value.status = 'SUCCESS'
        mock_async_result.return_value.ready.return_value = True
        mock_async_result.return_value.failed.return_value = False
        mock_async_result.return_value.successful.return_value = True
        mock_async_result.return_value.result = {}

        self.client.force_login(self.superuser)
        response = self.client.get('/api/admin/tasks/?active_only=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    @patch('AOTS.task_status.AsyncResult')
    def test_task_detail(self, mock_async_result):
        mock_async_result.return_value.status = 'PROGRESS'
        mock_async_result.return_value.ready.return_value = False
        mock_async_result.return_value.failed.return_value = False
        mock_async_result.return_value.successful.return_value = False
        mock_async_result.return_value.info = {'current': 2, 'total': 5, 'star_name': 'Target'}

        self.client.force_login(self.superuser)
        response = self.client.get('/api/admin/tasks/listed-task/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progress'], '2/5 (Target)')


class TaskStatusPayloadTests(TestCase):
    @patch('AOTS.task_status.AsyncResult')
    def test_build_task_status_payload_includes_registration(self, mock_async_result):
        mock_async_result.return_value.status = 'PENDING'
        mock_async_result.return_value.ready.return_value = False
        mock_async_result.return_value.failed.return_value = False
        mock_async_result.return_value.successful.return_value = False

        payload = build_task_status_payload('task-1', {
            'user_id': 1,
            'project_id': 2,
            'task_name': 'stars.tasks.fetch_gaia_bulk_task',
            'label': '3 star(s)',
            'created_at': '2026-01-01T12:00:00+00:00',
        })

        self.assertEqual(payload['task_display'], 'Gaia DR3 fetch')
        self.assertEqual(payload['label'], '3 star(s)')
