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

    def test_bulk_download_requires_star_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/observations/api-spec-download/',
            HTTP_PROJECTID=str(self.project.pk),
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_download_session_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/observations/api-spec-download/',
            HTTP_PROJECTID=str(self.project.pk),
            HTTP_STARIDLIST=str(self.star.pk),
        )
        self.assertIn(response.status_code, (200, 400))

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
