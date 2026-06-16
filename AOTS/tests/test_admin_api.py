from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from stars.models import Project

User = get_user_model()


class AdminApiPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
        )
        self.user = User.objects.create_user(
            username='normal',
            password='testpass123',
        )
        self.list_urls = [
            '/api/admin/users/',
            '/api/admin/projects/',
            '/api/admin/groups/',
            '/api/admin/tokens/',
            '/api/admin/log-entries/',
            '/api/admin/users/choices/',
            '/api/admin/permissions/',
        ]

    def test_anonymous_forbidden(self):
        for url in self.list_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, url)

    def test_normal_user_forbidden(self):
        self.client.force_login(self.user)
        for url in self.list_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, url)


class AdminUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
        )
        self.client.force_login(self.superuser)

    def test_user_crud_and_password(self):
        create = self.client.post(
            '/api/admin/users/',
            {
                'username': 'newbie',
                'email': 'newbie@test.com',
                'password': 'secret123',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        user_id = create.data['id']

        detail = self.client.get(f'/api/admin/users/{user_id}/')
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['username'], 'newbie')
        self.assertNotIn('password', detail.data)

        patch = self.client.patch(
            f'/api/admin/users/{user_id}/',
            {'note': 'Test note', 'is_student': True},
            format='json',
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertTrue(patch.data['is_student'])

        login_client = APIClient()
        logged_in = login_client.login(username='newbie', password='secret123')
        self.assertTrue(logged_in)

        delete = self.client.delete(f'/api/admin/users/{user_id}/')
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_self(self):
        response = self.client.delete(f'/api/admin/users/{self.superuser.pk}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminProjectApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
        )
        self.other = User.objects.create_user(username='member', password='testpass123')
        self.client.force_login(self.superuser)

    def test_project_crud_with_m2m(self):
        create = self.client.post(
            '/api/admin/projects/',
            {
                'name': 'Admin Project',
                'description': 'Created via admin API',
                'is_public': False,
                'readonly_users': [self.other.pk],
                'project_managers': [self.superuser.pk],
            },
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        pk = create.data['pk']
        self.assertTrue(create.data['slug'])

        project = Project.objects.get(pk=pk)
        self.assertIn(self.other, project.readonly_users.all())
        self.assertIn(self.superuser, project.project_managers.all())

        patch = self.client.patch(
            f'/api/admin/projects/{pk}/',
            {'readwrite_users': [self.other.pk]},
            format='json',
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertIn(self.other, project.readwrite_users.all())

        delete = self.client.delete(f'/api/admin/projects/{pk}/')
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)


class AdminGroupTokenLogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
        )
        self.user = User.objects.create_user(username='member', password='testpass123')
        self.client.force_login(self.superuser)

    def test_group_crud(self):
        create = self.client.post(
            '/api/admin/groups/',
            {'name': 'Editors', 'permissions': []},
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        group_id = create.data['id']

        patch = self.client.patch(
            f'/api/admin/groups/{group_id}/',
            {'name': 'Editors Renamed'},
            format='json',
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(Group.objects.get(pk=group_id).name, 'Editors Renamed')

    def test_token_create_and_delete(self):
        create = self.client.post(
            '/api/admin/tokens/',
            {'user': self.user.pk},
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        token_pk = create.data['pk']
        self.assertTrue(Token.objects.filter(pk=token_pk, user=self.user).exists())

        delete = self.client.delete(f'/api/admin/tokens/{token_pk}/')
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_log_entries_read_only(self):
        list_resp = self.client.get('/api/admin/log-entries/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)

        post_resp = self.client.post('/api/admin/log-entries/', {}, format='json')
        self.assertEqual(post_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_log_change_message_display(self):
        ct = ContentType.objects.get_for_model(Project)
        LogEntry.objects.create(
            user=self.superuser,
            content_type=ct,
            object_id='999',
            object_repr='Formatted Project',
            action_flag=CHANGE,
            change_message='[{"changed": {"fields": ["Readwrite users", "Project managers"]}}]',
        )
        LogEntry.objects.create(
            user=self.superuser,
            content_type=ct,
            object_id='998',
            object_repr='Added Project',
            action_flag=ADDITION,
            change_message='[{"added": {}}]',
        )

        response = self.client.get('/api/admin/log-entries/')
        rows = {row['object_repr']: row for row in response.data['results']}

        self.assertIn('Readwrite users', rows['Formatted Project']['change_message_display'])
        self.assertNotIn('[{"changed"', rows['Formatted Project']['change_message_display'])
        self.assertEqual(rows['Added Project']['change_message_display'], 'Added.')
        self.assertEqual(rows['Formatted Project']['action_flag_label'], 'Change')

    def test_permissions_grouped(self):
        response = self.client.get('/api/admin/permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_user_choices(self):
        response = self.client.get('/api/admin/users/choices/?search=member')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
