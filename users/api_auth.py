import logging

from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.response import Response

from .models import User

logger = logging.getLogger('AOTS.api_auth')


def Validate_API_key(public_key, secret_key):
    try:
        requesting_user = User.objects.get(api_key__iexact=public_key)
    except User.DoesNotExist:
        return None, False
    if check_password(secret_key, requesting_user.api_secret):
        return requesting_user, True
    return None, False


def authenticate_API_key(func):
    def wrapper(request, *args, **kwargs):
        public_key = request.META.get('HTTP_PUBLICAPIKEY')
        secret_key = request.META.get('HTTP_SECRETAPIKEY')
        user, validated = Validate_API_key(public_key, secret_key)
        if validated:
            logger.info(
                'API key auth succeeded for user_id=%s path=%s',
                user.pk,
                request.path,
            )
            login(request, user)
            return func(request, *args, **kwargs)
        logger.warning('API key auth failed for path=%s', request.path)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    return wrapper
