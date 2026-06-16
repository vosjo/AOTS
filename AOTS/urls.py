"""AOTS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
   https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
   1. Add an import:  from my_app import views
   2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
   1. Add an import:  from other_app.views import Home
   2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
   1. Import the include() function: from django.conf.urls import url, include
   2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
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
)
from AOTS.spa_views import spa_index
from AOTS.views import health_check
from dash.api_views import dashboard_bootstrap
from stars import views as star_views
from stars.api.views import ProjectViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)

urlpatterns = [
                  path('health/', health_check, name='health'),
                  path('', RedirectView.as_view(pattern_name='projects')),
                  path(
                      "robots.txt",
                      TemplateView.as_view(
                          template_name="robots.txt",
                          content_type="text/plain",
                      ),
                  ),

                  path(
                      'w/documentation/',
                      TemplateView.as_view(
                          template_name='documentation.html'
                      )
                  ),
                  path(
                      'w/projects/',
                      star_views.project_list,
                      name='projects',
                  ),
                  path(
                      'w/<slug:project>/',
                      RedirectView.as_view(pattern_name='dash:dashboard')
                  ),
                  path(
                      'w/<slug:project>/systems/',
                      include('stars.urls', namespace='systems')
                  ),
                  path(
                      'w/<slug:project>/observations/',
                      include(
                          'observations.urls',
                          namespace='observations'
                      )
                  ),
                  path(
                      'w/<slug:project>/dash/',
                      include('dash.urls', namespace='dash')
                  ),
                  path(
                      'w/<slug:project>/analysis/',
                      include('analysis.urls', namespace='analysis')
                  ),
                  path(
                      'w/<slug:project>/dashboard/',
                      RedirectView.as_view(pattern_name='dash:dashboard')
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
                  path(
                      'api/dash/<slug:project_slug>/',
                      dashboard_bootstrap,
                      name='api-dashboard',
                  ),

                  path('api/', include(router.urls), name='project-api'),
                  path(
                      'api/systems/',
                      include("stars.api.urls", namespace='systems-api')
                  ),
                  path(
                      'api/observations/',
                      include(
                          "observations.api.urls",
                          namespace='observations-api'
                      )
                  ),
                  path(
                      'api/analysis/',
                      include(
                          "analysis.api.urls",
                          namespace='analysis-api'
                      )
                  ),
                  path(
                      'users/',
                      include(
                          "users.urls",
                          namespace='users'
                      )
                  ),

                  path(r'admin/', admin.site.urls),

                  # path('', RedirectView.as_view(url='/stars/stars/', permanent=False)),
                  # path('stars/', include('stars.urls', namespace='stars'), name='stars'),
                  # path('observations/', include('observations.urls'), name='observations'),
                  # path('analysis/', include('analysis.urls'), name='analysis'),

                  # path(r'api/stars/', include("stars.api.urls"), name='stars-api'),
                  # path(r'api/observations/', include("observations.api.urls"), name='observations-api'),
                  # path(r'api/analysis/', include("analysis.api.urls"), name='analysis-api'),

                  # path(r'^login/$', auth_views.login, name='login'),
                  # path(r'^logout/$', auth_views.logout, {'next_page': '/stars/stars'}, name='logout'),
                  # path(r'^change-password/$', auth_views.password_change, name='change-pwd'),
                  # path(r'^password-change-done/$', auth_views.password_change_done, name='password_change_done'),

                  # include all relevant user login/logout stuff. This includes:
                  #  accounts/login/ [name='login']
                  #  accounts/logout/ [name='logout']
                  #  accounts/password_change/ [name='password_change']
                  #  accounts/password_change/done/ [name='password_change_done']
                  #  accounts/password_reset/ [name='password_reset']
                  #  accounts/password_reset/done/ [name='password_reset_done']
                  #  accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
                  #  accounts/reset/done/ [name='password_reset_complete']
                  path('accounts/', include('django.contrib.auth.urls')),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'AOTS_SPA_CUTOVER', False):
    urlpatterns += [
        re_path(
            r'^app/(?P<path>.*)$',
            RedirectView.as_view(url='/%(path)s', permanent=False),
        ),
        re_path(r'^w/.*$', spa_index),
        re_path(r'^users/.*$', spa_index),
        re_path(
            r'^accounts/(login|password_change|password_change/done)/?$',
            spa_index,
        ),
        re_path(r'^w/documentation/?$', spa_index),
    ]
else:
    urlpatterns += [
        re_path(r'^app/.*$', spa_index),
    ]
