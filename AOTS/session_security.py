"""Session helpers for auth security (invalidate other sessions on password change)."""

from __future__ import annotations

from django.contrib.auth import update_session_auth_hash
from django.contrib.sessions.models import Session
from django.utils import timezone


def flush_other_sessions(user, request=None):
    """
    Delete all sessions belonging to ``user`` except the current request session.
    Call after password change/reset. When ``request`` is provided, refresh the
    current session hash so the user stays logged in.
    """
    keep_key = getattr(getattr(request, 'session', None), 'session_key', None)
    user_id = str(user.pk)
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if str(data.get('_auth_user_id')) != user_id:
            continue
        if keep_key and session.session_key == keep_key:
            continue
        session.delete()
    if request is not None and request.user.is_authenticated:
        update_session_auth_hash(request, user)
