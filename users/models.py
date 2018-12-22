from django.db import models


from django.contrib.auth.models import AbstractUser


def get_sentinel_user():
   """
   Sets a default 'deleted' user if the user is deleted.
   """
   return User().objects.get_or_create(username='deleted')[0]


class User(AbstractUser):
    pass
