
from django.conf import settings


def get_sentinel_user():
   """
   Sets a default 'deleted' user if the user is deleted.
   """
   return settings.AUTH_USER_MODEL().objects.get_or_create(username='deleted')[0]

def get_unknown_user():
   """
   Gets the unknown user to be used as a default for the added_by field
   """
   return settings.AUTH_USER_MODEL().objects.get_or_create(username='unknown')[0] 
