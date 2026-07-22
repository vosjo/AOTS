import random
import string

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


def _project_logo_upload_to(instance, filename):
    from AOTS.media_signing import opaque_upload_to
    return opaque_upload_to('public/projects')(instance, filename)


class Project(models.Model):
    """
    A project that contains a set of stars.
    """

    name = models.CharField(max_length=100, unique=True)

    slug = models.SlugField(max_length=20, unique=True)

    description = models.TextField(default='')

    logo = models.FileField(
        upload_to=_project_logo_upload_to,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'webp'])],
    )

    is_public = models.BooleanField(default=True)

    starmap_cache_version = models.PositiveIntegerField(default=0)

    readonly_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readonly_projects', blank=True)
    readwriteown_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readwriteown_projects',
                                                blank=True)
    readwrite_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readwrite_projects', blank=True)
    project_managers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='managed_projects', blank=True)

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    def delete(self, using=None, keep_parents=False):
        from stars.services.project_io import prepare_project_deletion

        prepare_project_deletion(self)
        return super().delete(using=using, keep_parents=keep_parents)

    # -- representation of self
    def __str__(self):
        return self.name


@receiver(pre_save, sender=Project)
def set_project_slug(sender, **kwargs):
    """
    Create a unique slug based on the name of the project
    if a slug already exists a number is added until a unique slug is found.
    """

    if kwargs.get('raw', False):
        return

    project = kwargs['instance']

    if project.slug != '':
        return

    unique_slug = slugify(project.name[0:17], allow_unicode=False)
    slug = slugify(project.name[0:17], allow_unicode=False)

    extension = 1
    while Project._default_manager.filter(slug=unique_slug).exists() and extension <= 99:
        unique_slug = '{}-{}'.format(slug, extension)
        extension += 1
    if extension > 99:
        unique_slug = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(20)
        )

    project.slug = unique_slug
