from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from users.models import User


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    rate = '10/min'


class AuthApiKeyRateThrottle(UserRateThrottle):
    scope = 'auth_api_key'
    rate = '5/min'


class PasswordChangeRateThrottle(UserRateThrottle):
    scope = 'password_change'
    rate = '5/min'


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = 'password_reset'
    rate = '5/hour'


def _password_reset_url(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    return f'{protocol}://{domain}/accounts/reset/{uid}/{token}/'


def _send_password_reset_emails(form, request):
    email_field = form.cleaned_data['email']
    for user in form.get_users(email_field):
        context = {
            'user': user,
            'reset_url': _password_reset_url(request, user),
            'site_name': 'AOTS',
        }
        subject = render_to_string('emails/password_reset_subject.txt', context).strip()
        body = render_to_string('emails/password_reset_body.txt', context)
        send_mail(
            subject,
            body,
            None,
            [user.email],
            fail_silently=False,
        )


def _user_from_reset_uid(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def _me_payload(user):
    if user.is_anonymous:
        return {'authenticated': False}
    return {
        'authenticated': True,
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
        'has_api_secret': bool(user.api_secret),
        'has_api_key': bool(user.api_key),
    }


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    return Response(_me_payload(request.user))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_credentials(request):
    """Return API public key (secret is never returned after creation)."""
    return Response({
        'api_key': request.user.api_key,
        'has_api_secret': bool(request.user.api_secret),
    })


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def auth_csrf(request):
    return Response({'csrfToken': get_token(request)})


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def app_bootstrap(request):
    return Response({
        'csrfToken': get_token(request),
        'testInstallation': getattr(settings, 'AOTS_TEST_INSTALLATION', False),
    })


@ensure_csrf_cookie
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
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
    return Response({
        **_me_payload(user),
        'csrfToken': get_token(request),
    })


@ensure_csrf_cookie
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    logout(request)
    return Response({
        'authenticated': False,
        'csrfToken': get_token(request),
    })


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
@throttle_classes([AuthApiKeyRateThrottle])
def auth_api_key(request):
    api_key = get_random_string(32, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    api_secret = get_random_string(64, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    request.user.api_key = api_key
    request.user.api_secret = make_password(api_secret)
    request.user.save(update_fields=['api_key', 'api_secret'])
    return Response({'api_key': api_key, 'api_secret': api_secret})


@ensure_csrf_cookie
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([PasswordChangeRateThrottle])
def password_change_api(request):
    old = request.data.get('old_password', '')
    new1 = request.data.get('new_password1', '')
    new2 = request.data.get('new_password2', '')
    if not request.user.check_password(old):
        return Response({'old_password': ['Wrong password.']}, status=400)
    if new1 != new2:
        return Response({'new_password2': ['Passwords do not match.']}, status=400)
    try:
        validate_password(new1, user=request.user)
    except DjangoValidationError as exc:
        return Response({'new_password1': list(exc.messages)}, status=400)
    request.user.set_password(new1)
    request.user.save()
    from AOTS.session_security import flush_other_sessions
    flush_other_sessions(request.user, request=request)
    login(request, request.user)
    return Response({
        'detail': 'Password changed. Other sessions have been signed out.',
        'csrfToken': get_token(request),
    })


@ensure_csrf_cookie
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_request(request):
    email = (request.data.get('email') or '').strip()
    form = PasswordResetForm({'email': email})
    if not form.is_valid():
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    _send_password_reset_emails(form, request)
    return Response({
        'detail': (
            'If an account exists with that email address, '
            'you will receive a password reset link shortly.'
        ),
    })


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_validate(request):
    uidb64 = request.query_params.get('uid', '')
    token = request.query_params.get('token', '')
    user = _user_from_reset_uid(uidb64)
    if user is None or not default_token_generator.check_token(user, token):
        return Response(
            {'detail': 'Invalid or expired reset link.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response({'valid': True})


@ensure_csrf_cookie
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_confirm(request):
    uidb64 = request.data.get('uid', '')
    token = request.data.get('token', '')
    new1 = request.data.get('new_password1', '')
    new2 = request.data.get('new_password2', '')

    user = _user_from_reset_uid(uidb64)
    if user is None or not default_token_generator.check_token(user, token):
        return Response(
            {'detail': 'Invalid or expired reset link.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if new1 != new2:
        return Response({'new_password2': ['Passwords do not match.']}, status=400)
    try:
        validate_password(new1, user=user)
    except DjangoValidationError as exc:
        return Response({'new_password1': list(exc.messages)}, status=400)

    user.set_password(new1)
    user.save()
    from AOTS.session_security import flush_other_sessions
    flush_other_sessions(user, request=None)
    return Response({
        'detail': (
            'Password has been reset. Other sessions have been signed out. '
            'API key credentials were not rotated; regenerate them if the account may have been compromised.'
        ),
    })
