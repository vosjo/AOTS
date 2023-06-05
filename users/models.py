from django.contrib.auth.models import AbstractUser
from django.db import models

from stars import models as star_models


def get_sentinel_user():
    """
    Sets a default 'deleted' user if the user is deleted.
    """
    return User().objects.get_or_create(username='deleted')[0]


# deprecated??
def get_unknown_user():
    """
    Gets the unknown user to be used as a default for the added_by field
    """
    return User().objects.get_or_create(username='unknown')[0]


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    api_key = models.CharField(max_length=120, blank=True, null=True)
    api_secret = models.CharField(max_length=140, blank=True, null=True)
    profile_picture = models.FileField(upload_to='profile_pictures/', null=True, blank=True)

    note = models.TextField(default='')

    def get_read_projects(self):
        if self.is_superuser:
            return star_models.Project.objects.all()
        else:
            return self.readonly_projects.all().union(self.readwriteown_projects.all(),
                                                      self.readwrite_projects.all())

    def can_read(self, project):
        """
        Returns true if this user has read access to objects of this project
        """

        if project.is_public or self.is_superuser:
            # Public projects can be read by everyone
            return True
        elif project in self.readonly_projects.all() or \
                project in self.readwriteown_projects.all() or \
                project in self.readwrite_projects.all():
            # private projects require read access
            return True
        else:
            return False

    def can_add(self, project):
        """
        Returns true if this user can add new objects to this project
        """

        if self.is_superuser:
            return True
        elif project in self.readwriteown_projects.all() or \
                project in self.readwrite_projects.all():
            return True
        else:
            return False

    def can_edit(self, obj):
        """
        Returns true if this user can edit this specific object
        """
        if self.is_superuser:
            return True
        elif obj.project in self.readwrite_projects.all():
            return True
        elif obj.project in self.readwriteown_projects.all() and \
                obj.history.earliest().history_user == self:
            return True
        else:
            return False

    def can_delete(self, obj):
        """
        Returns true if this user can delete this specific object
        """
        if self.is_superuser:
            return True
        elif obj.project in self.readwrite_projects.all() and \
                obj.history.earliest().history_user == self:
            return True
        elif obj.project in self.readwriteown_projects.all() and \
                obj.history.earliest().history_user == self:
            return True
        elif obj.project in self.managed_projects.all():
            return True
        else:
            return False
