 
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^spectra/$', views.spectra_list, name='spectra_list'),
    url(r'^spectra/(?P<spectrum_id>[0-9]+)/$', views.spectra_detail, name='spectra_detail'),
    url(r'^specfiles/$', views.specfile_list, name='specfile_list'),
]