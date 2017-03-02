"""BiMoT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
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
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^stars/', include('stars.urls', namespace='stars'), name='stars'),
    url(r'^spectra/', include('spectra.urls', namespace='spectra'), name='spectra'),
    url(r'^analysis/', include('analysis.urls', namespace='analysis'), name='analysis'),
    url(r'^admin/', admin.site.urls),
    
    url(r'^api/stars/', include("stars.api.urls", namespace='stars-api')),
    url(r'^api/spectra/', include("spectra.api.urls", namespace='spectra-api')),
    url(r'^api/analysis/', include("analysis.api.urls", namespace='analysis-api')),
    
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/stars/stars'}, name='logout'),
    url(r'^change-password/$', auth_views.password_change, name='change-pwd'),
    url(r'^password-change-done/$', auth_views.password_change_done, name='password_change_done'),
]
