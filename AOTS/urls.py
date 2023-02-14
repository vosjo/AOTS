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
from django.urls import include, path
# from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView, TemplateView
from rest_framework import routers

from stars import views as star_views
from stars.api.views import ProjectViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)

urlpatterns = [
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
                     RedirectView.as_view(pattern_name='analysis:dashboard')
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
                     'w/<slug:project>/observations/',
                     RedirectView.as_view(
                        pattern_name='observations:observatory_list'
                        )
                     ),
                  path(
                     'w/<slug:project>/analysis/',
                     include('analysis.urls', namespace='analysis')
                     ),
                  path(
                     'w/<slug:project>/dashboard/',
                     RedirectView.as_view(pattern_name='analysis:dashboard')
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
