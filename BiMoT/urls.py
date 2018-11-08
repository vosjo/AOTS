"""BiMoT URL Configuration

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
from django.urls import include, path
from django.contrib import admin
#from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from stars import views as star_views

from rest_framework import routers
from stars.api.views import ProjectViewSet
router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)


urlpatterns = [
   path('', RedirectView.as_view(pattern_name='projects')),
   #path('w/<slug:project>', RedirectView.as_view(url='{}/stars/stars/', permanent=False)),
   path('w/projects/', star_views.project_list, name='projects'),
   path('w/<slug:project>/', RedirectView.as_view(pattern_name='systems:star_list')),
   path('w/<slug:project>/systems/', include('stars.urls', namespace='systems')),
   path('w/<slug:project>/observations/', include('spectra.urls', namespace='observations')),
   path('w/<slug:project>/analysis/', include('analysis.urls', namespace='analysis')),
   
   path('api/', include(router.urls), name='project-api'),
   path('api/stars/', include("stars.api.urls", namespace='systems-api') ),
   path('api/observations/', include("spectra.api.urls", namespace='observations-api') ),
   path('api/analysis/', include("analysis.api.urls", namespace='analysis-api') ),
   
   path(r'admin/', admin.site.urls),
   
   #path('', RedirectView.as_view(url='/stars/stars/', permanent=False)),
   #path('stars/', include('stars.urls', namespace='stars'), name='stars'),
   #path('spectra/', include('spectra.urls'), name='spectra'),
   #path('analysis/', include('analysis.urls'), name='analysis'),
   
   #path(r'api/stars/', include("stars.api.urls"), name='stars-api'),
   #path(r'api/spectra/', include("spectra.api.urls"), name='spectra-api'),
   #path(r'api/analysis/', include("analysis.api.urls"), name='analysis-api'),
   
   #path(r'^login/$', auth_views.login, name='login'),
   #path(r'^logout/$', auth_views.logout, {'next_page': '/stars/stars'}, name='logout'),
   #path(r'^change-password/$', auth_views.password_change, name='change-pwd'),
   #path(r'^password-change-done/$', auth_views.password_change_done, name='password_change_done'),
   
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
   
   
   
]
