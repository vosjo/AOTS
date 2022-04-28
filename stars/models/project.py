from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from six import python_2_unicode_compatible

from users.models import get_sentinel_user


# Create your models here.

@python_2_unicode_compatible  # to support Python 2
class Project(models.Model):
    """
    A project that contains a set of stars.
    """

    name = models.CharField(max_length=100, unique=True)

    slug = models.SlugField(max_length=20, unique=True)

    description = models.TextField(default='')

    logo = models.FileField(upload_to='projects/', null=True, blank=True)

    is_public = models.BooleanField(default=True)

    readonly_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readonly_projects', blank=True)
    readwriteown_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readwriteown_projects',
                                                blank=True)
    readwrite_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='readwrite_projects', blank=True)
    project_managers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='managed_projects', blank=True)

    # -- bookkeeping
    added_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), null=True,
                                 related_name='added_projects')

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
    while Project._default_manager.filter(**{'slug': unique_slug}).exists() or extension > 99:
        unique_slug = '{}-{}'.format(slug, extension)
        extension += 1
    if extension > 99:
        unique_slug = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))

    project.slug = unique_slug
