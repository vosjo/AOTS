# Authentication function
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework import status
from .models import User


def Validate_API_key(public_key, secret_key):
    try:
        requesting_user = User.objects.get(api_key__iexact=public_key)
    except:
        return None, False
    if check_password(secret_key, requesting_user.api_secret):
        return requesting_user, True
    else:
        return None, False


def authenticate_API_key(func):
    def wrapper(request, *args, **kwargs):
        # TODO: add API key tracking
        public_key = request.META.get('HTTP_PUBLICAPIKEY')  # Assuming the API key is passed in the request header
        secret_key = request.META.get('HTTP_SECRETAPIKEY')
        user, validated = Validate_API_key(public_key, secret_key)
        if validated:
            login(request, user)
            return func(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    return wrapper
