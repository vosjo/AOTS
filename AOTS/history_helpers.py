"""Helpers for django-simple-history actor attribution."""


def find_history_user(instance):
    """Return the most relevant user for an object's history, or None."""
    manager = getattr(instance, 'history', None)
    if manager is None:
        return None
    try:
        latest = manager.latest()
    except manager.model.DoesNotExist:
        return None
    if latest.history_user_id is not None:
        return latest.history_user
    for record in manager.order_by('-history_date'):
        if record.history_user_id is not None:
            return record.history_user
    return None


def history_actor_username(instance, *, missing='system'):
    """Username (or fallback label) for dashboard changelog display."""
    user = find_history_user(instance)
    if user is None:
        return missing
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return full_name or user.username


def history_actor_for_changelog(instance, *, missing='system'):
    """Return (user_or_none, display_name) for dashboard changelog entries."""
    user = find_history_user(instance)
    if user is None:
        return None, missing
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return user, full_name or user.username
