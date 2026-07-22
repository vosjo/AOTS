from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from AOTS.project_resolution import get_object_project
from stars import models as star_models


def get_sentinel_user():
    """
    Sets a default 'deleted' user if the user is deleted.
    """
    return User.objects.get_or_create(username='deleted')[0]


# deprecated??
def get_unknown_user():
    """
    Gets the unknown user to be used as a default for the added_by field
    """
    return User.objects.get_or_create(username='unknown')[0]


def _profile_picture_upload_to(instance, filename):
    from AOTS.media_signing import opaque_upload_to
    return opaque_upload_to('public/profile_pictures')(instance, filename)


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    api_key = models.CharField(max_length=120, blank=True, null=True, unique=True)
    api_secret = models.CharField(max_length=140, blank=True, null=True)
    profile_picture = models.FileField(
        upload_to=_profile_picture_upload_to,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'webp'])],
    )

    note = models.TextField(default='')

    def get_read_projects(self):
        if self.is_superuser:
            return star_models.Project.objects.all()
        else:
            return self.readonly_projects.all().union(
                self.readwriteown_projects.all(),
                self.readwrite_projects.all(),
            )

    def _project_in_user_set(self, project, relation_name):
        return self.__class__.objects.filter(
            pk=self.pk,
            **{f'{relation_name}__pk': project.pk},
        ).exists()

    def can_read(self, project):
        """
        Returns true if this user has read access to objects of this project
        """
        if project.is_public or self.is_superuser:
            return True
        return (
            self._project_in_user_set(project, 'readonly_projects')
            or self._project_in_user_set(project, 'readwriteown_projects')
            or self._project_in_user_set(project, 'readwrite_projects')
        )

    def can_add(self, project):
        """
        Returns true if this user can add new objects to this project
        """
        if self.is_superuser:
            return True
        return (
            self._project_in_user_set(project, 'readwriteown_projects')
            or self._project_in_user_set(project, 'readwrite_projects')
        )

    def _object_creator(self, obj):
        """Return the user who originally created obj, or None if unknown."""
        if not hasattr(obj, 'history'):
            return None
        record = obj.history.order_by('history_date').first()
        if record is None:
            return None
        return record.history_user

    def can_edit(self, obj):
        """
        Returns true if this user can edit this specific object
        """
        if self.is_superuser:
            return True
        project = get_object_project(obj)
        if self._project_in_user_set(project, 'readwrite_projects'):
            return True
        creator = self._object_creator(obj)
        if (
            creator is not None
            and self._project_in_user_set(project, 'readwriteown_projects')
            and creator == self
        ):
            return True
        return False

    def can_delete(self, obj):
        """
        Returns true if this user can delete this specific object
        """
        if self.is_superuser:
            return True
        project = get_object_project(obj)
        creator = self._object_creator(obj)
        if (
            creator is not None
            and self._project_in_user_set(project, 'readwrite_projects')
            and creator == self
        ):
            return True
        if (
            creator is not None
            and self._project_in_user_set(project, 'readwriteown_projects')
            and creator == self
        ):
            return True
        if self._project_in_user_set(project, 'managed_projects'):
            return True
        return False
