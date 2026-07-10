"""AOTS URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from AOTS.api_auth import (
    app_bootstrap,
    auth_api_key,
    auth_csrf,
    auth_login,
    auth_logout,
    auth_token,
    me,
    password_change_api,
    password_reset_confirm,
    password_reset_request,
    password_reset_validate,
)
from AOTS.spa_views import spa_index
from AOTS.views import health_check
from dash.api_views import dashboard_bootstrap, dashboard_starmap
from stars.api.views import ProjectViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)

urlpatterns = [
    path('health/', health_check, name='health'),
    path(
        'robots.txt',
        TemplateView.as_view(
            template_name='robots.txt',
            content_type='text/plain',
        ),
    ),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    path('api/me/', me, name='api-me'),
    path('api/bootstrap/', app_bootstrap, name='api-bootstrap'),
    path('api/admin/', include('AOTS.admin_api.urls')),
    path('api/auth/csrf/', auth_csrf, name='api-auth-csrf'),
    path('api/auth/login/', auth_login, name='api-auth-login'),
    path('api/auth/logout/', auth_logout, name='api-auth-logout'),
    path('api/auth/token/', auth_token, name='api-auth-token'),
    path('api/auth/api-key/', auth_api_key, name='api-auth-api-key'),
    path('api/auth/password-change/', password_change_api, name='api-password-change'),
    path('api/auth/password-reset/', password_reset_request, name='api-password-reset'),
    path('api/auth/password-reset/validate/', password_reset_validate, name='api-password-reset-validate'),
    path('api/auth/password-reset/confirm/', password_reset_confirm, name='api-password-reset-confirm'),
    path(
        'api/dash/<slug:project_slug>/',
        dashboard_bootstrap,
        name='api-dashboard',
    ),
    path(
        'api/dash/<slug:project_slug>/starmap/',
        dashboard_starmap,
        name='api-dashboard-starmap',
    ),

    path('api/', include(router.urls), name='project-api'),
    path(
        'api/systems/',
        include('stars.api.urls', namespace='systems-api'),
    ),
    path(
        'api/observations/',
        include('observations.api.urls', namespace='observations-api'),
    ),
    path(
        'api/analysis/',
        include('analysis.api.urls', namespace='analysis-api'),
    ),

    path(
        'api/interop/',
        include('interop.api.urls', namespace='interop-api'),
    ),

    path('django-admin/', admin.site.urls),

    path('', RedirectView.as_view(url='/w/projects/', permanent=False)),
    re_path(r'^accounts/.*$', spa_index),
    path('w/projects/', spa_index, name='projects'),
    re_path(r'^w/.*$', spa_index),
    re_path(r'^users/.*$', spa_index),
    re_path(r'^admin/.*$', spa_index),
    re_path(
        r'^app/(?P<path>.*)$',
        RedirectView.as_view(url='/%(path)s', permanent=False),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
