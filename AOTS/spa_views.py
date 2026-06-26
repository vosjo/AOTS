from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def spa_index(request, *args, **kwargs):
    return render(request, 'spa/index.html', {
        'csrf_token': get_token(request),
        'vite_dev': getattr(settings, 'VITE_DEV', False),
        'test_installation': getattr(settings, 'AOTS_TEST_INSTALLATION', False),
        'router_base': '/',
    })
