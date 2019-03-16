 

from django.urls import path

from . import views

app_name = 'observations'
urlpatterns = [
    path('spectra/', views.spectra_list, name='spectra_list'),
    path('spectra/<int:spectrum_id>/', views.spectrum_detail, name='spectrum_detail'),
    path('specfiles/', views.specfile_list, name='specfile_list'),
    path('spectra/new', views.add_spectra, name='spectra_new'),
    path('lightcurves/', views.lightcurve_list, name='lightcurve_list'),
    path('lightcurves/<int:lightcurve_id>/', views.lightcurve_detail, name='lightcurve_detail'),
    path('observatories/', views.observatory_list, name='observatory_list'),
]
