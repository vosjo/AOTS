from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User


def _me_payload(user):
    if user.is_anonymous:
        return {'authenticated': False}
    return {
        'authenticated': True,
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
        'api_key': user.api_key,
        'has_api_secret': bool(user.api_secret),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def me(request):
    return Response(_me_payload(request.user))


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def auth_csrf(request):
    return Response({'csrfToken': get_token(request)})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def app_bootstrap(request):
    return Response({
        'csrfToken': get_token(request),
        'testInstallation': getattr(settings, 'AOTS_TEST_INSTALLATION', False),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    login(request, user)
    return Response(_me_payload(user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    logout(request)
    return Response({'authenticated': False})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def auth_token(request):
    token, _created = Token.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        token.delete()
        token = Token.objects.create(user=request.user)
    return Response({'token': token.key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_api_key(request):
    api_key = get_random_string(32, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    api_secret = get_random_string(64, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    request.user.api_key = api_key
    request.user.api_secret = make_password(api_secret)
    request.user.save(update_fields=['api_key', 'api_secret'])
    return Response({'api_key': api_key, 'api_secret': api_secret})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change_api(request):
    old = request.data.get('old_password', '')
    new1 = request.data.get('new_password1', '')
    new2 = request.data.get('new_password2', '')
    if not request.user.check_password(old):
        return Response({'old_password': ['Wrong password.']}, status=400)
    if new1 != new2:
        return Response({'new_password2': ['Passwords do not match.']}, status=400)
    if len(new1) < 8:
        return Response({'new_password1': ['Password too short.']}, status=400)
    request.user.set_password(new1)
    request.user.save()
    login(request, request.user)
    return Response({'detail': 'Password changed.'})
