from django.db import models

from django.contrib.auth.models import AbstractUser

def get_sentinel_user():
   """
   Sets a default 'deleted' user if the user is deleted.
   """
   return User().objects.get_or_create(username='deleted')[0]

def get_unknown_user():
   """
   Gets the unknown user to be used as a default for the added_by field
   """
   return User().objects.get_or_create(username='unknown')[0] 



class User(AbstractUser):
   
   is_student = models.BooleanField(default=False)
   
   note = models.TextField(default='')
   
