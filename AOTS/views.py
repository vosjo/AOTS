from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Anonymous health probe returns only status.
    Staff users additionally receive a database connectivity flag.
    """
    user = getattr(request, 'user', None)
    is_staff = bool(user and getattr(user, 'is_staff', False))

    if not is_staff:
        return JsonResponse({'status': 'ok'})

    db_ok = False
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            db_ok = cursor.fetchone()[0] == 1
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            'status': 'ok' if db_ok else 'error',
            'database': db_ok,
        },
        status=status_code,
    )
