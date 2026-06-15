from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from AOTS.custom_permissions import IsAllowedOnProject, get_allowed_objects_to_view_for_user
from analysis.models import Parameter
from stars.models import Project, Star

User = get_user_model()


class GetAllowedObjectsTests(TestCase):
    def setUp(self):
        self.public_project = Project.objects.create(
            name='PublicProject',
            slug='public-project',
            is_public=True,
        )
        self.private_project = Project.objects.create(
            name='PrivateProject',
            slug='private-project',
            is_public=False,
        )
        self.public_star = Star.objects.create(
            name='PublicStar',
            project=self.public_project,
            ra=0.0,
            dec=0.0,
        )
        self.private_star = Star.objects.create(
            name='PrivateStar',
            project=self.private_project,
            ra=1.0,
            dec=1.0,
        )
        self.readonly_user = User.objects.create_user(
            username='readonly',
            password='testpass123',
        )
        self.private_project.readonly_users.add(self.readonly_user)

    def test_anonymous_user_sees_only_public_objects(self):
        qs = Star.objects.all()
        visible = get_allowed_objects_to_view_for_user(qs, AnonymousUser())

        self.assertIn(self.public_star, visible)
        self.assertNotIn(self.private_star, visible)

    def test_logged_in_user_sees_public_and_permitted_private_objects(self):
        qs = Star.objects.all()
        visible = get_allowed_objects_to_view_for_user(qs, self.readonly_user)

        self.assertIn(self.public_star, visible)
        self.assertIn(self.private_star, visible)

    def test_logged_in_user_without_private_access_sees_only_public(self):
        other_user = User.objects.create_user(
            username='other',
            password='testpass123',
        )
        qs = Star.objects.all()
        visible = get_allowed_objects_to_view_for_user(qs, other_user)

        self.assertIn(self.public_star, visible)
        self.assertNotIn(self.private_star, visible)


class IsAllowedOnProjectTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAllowedOnProject()
        self.project = Project.objects.create(
            name='PermProject',
            slug='perm-project',
            is_public=False,
        )
        self.readwrite_user = User.objects.create_user(
            username='readwrite',
            password='testpass123',
        )
        self.readonly_user = User.objects.create_user(
            username='readonlyperm',
            password='testpass123',
        )
        self.project.readwrite_users.add(self.readwrite_user)
        self.project.readonly_users.add(self.readonly_user)
        self.star = Star.objects.create(
            name='PermStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )

    def _drf_request(self, method, user, data=None):
        if method == 'get':
            django_request = self.factory.get('/')
        elif method == 'patch':
            django_request = self.factory.patch('/')
        else:
            django_request = self.factory.post('/', data or {})
        force_authenticate(django_request, user=user)
        drf_request = Request(django_request)
        if data is not None:
            drf_request._full_data = data
        return drf_request

    def test_readonly_user_can_read_object(self):
        request = self._drf_request('get', self.readonly_user)
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.star)
        )

    def test_anonymous_user_cannot_read_private_object(self):
        django_request = self.factory.get('/')
        django_request.user = AnonymousUser()
        request = Request(django_request)
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.star)
        )

    def test_readwrite_user_can_edit_object(self):
        request = self._drf_request('patch', self.readwrite_user)
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.star)
        )

    def test_readonly_user_cannot_edit_object(self):
        request = self._drf_request('patch', self.readonly_user)
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.star)
        )

    def test_readwrite_user_can_create_in_project(self):
        request = self._drf_request(
            'post',
            self.readwrite_user,
            data={'project': self.project.pk},
        )
        self.assertTrue(self.permission.has_permission(request, None))

    def test_readwrite_user_can_create_when_only_star_is_given(self):
        request = self._drf_request(
            'post',
            self.readwrite_user,
            data={'star': self.star.pk},
        )
        self.assertTrue(self.permission.has_permission(request, None))

    def test_readonly_user_cannot_create_in_project(self):
        request = self._drf_request(
            'post',
            self.readonly_user,
            data={'project': self.project.pk},
        )
        self.assertFalse(self.permission.has_permission(request, None))

    def test_readwrite_user_can_patch_project(self):
        request = self._drf_request('patch', self.readwrite_user)
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.project)
        )

    def test_readwrite_user_can_edit_parameter(self):
        parameter = Parameter.objects.create(
            star=self.star,
            name='logg',
            component=1,
            value=4.0,
            error=0.1,
            unit='cgs',
        )
        request = self._drf_request('patch', self.readwrite_user)
        self.assertTrue(
            self.permission.has_object_permission(request, None, parameter)
        )
        self.assertTrue(self.readwrite_user.can_edit(parameter))
