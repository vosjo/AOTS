import logging

from django.contrib.auth.hashers import check_password
from rest_framework import authentication, exceptions

from .models import User

logger = logging.getLogger('AOTS.api_auth')


def validate_api_key(public_key, secret_key):
    requesting_user = (
        User.objects.filter(api_key__iexact=public_key).order_by('pk').first()
    )
    if requesting_user is None:
        return None, False
    if check_password(secret_key, requesting_user.api_secret):
        return requesting_user, True
    return None, False


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
  Authenticate via HTTP_PUBLICAPIKEY and HTTP_SECRETAPIKEY headers.
  Does not create a Django session (stateless for API clients).
    """

    keyword_public = 'HTTP_PUBLICAPIKEY'
    keyword_secret = 'HTTP_SECRETAPIKEY'

    def authenticate(self, request):
        public_key = request.META.get(self.keyword_public)
        secret_key = request.META.get(self.keyword_secret)
        if not public_key or not secret_key:
            return None

        user, validated = validate_api_key(public_key, secret_key)
        if not validated:
            logger.warning('API key auth failed for path=%s', request.path)
            raise exceptions.AuthenticationFailed('Invalid API key credentials.')

        logger.info(
            'API key auth succeeded for user_id=%s path=%s',
            user.pk,
            request.path,
        )
        return (user, None)
