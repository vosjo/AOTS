 

from django.urls import path

from . import views

app_name = 'spectra'
urlpatterns = [
    path('spectra/', views.spectra_list, name='spectra_list'),
    path('spectra/<int:spectrum_id>/', views.spectra_detail, name='spectra_detail'),
    path('specfiles/', views.specfile_list, name='specfile_list'),
]
