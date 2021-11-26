

from django.urls import path

from . import views

app_name = 'observations'
urlpatterns = [
    #   Spectra
    path('spectra/', views.spectra_list, name='spectra_list'),
    path(
        'spectra/<int:spectrum_id>/',
        views.spectrum_detail,
        name='spectrum_detail',
        ),
    path('spectra/new', views.add_spectra, name='spectra_new'),
    #   SpecFiles
    path('specfiles/', views.specfile_list, name='specfile_list'),
    #   RawSpecFiles
    path('rawspecfiles/', views.rawspecfile_list, name='rawspecfile_list'),
    #   Lightcurves
    path('lightcurves/', views.lightcurve_list, name='lightcurve_list'),
    path(
        'lightcurves/<int:lightcurve_id>/',
        views.lightcurve_detail,
        name='lightcurve_detail',
        ),
    #   Observatories
    path('observatories/', views.observatory_list, name='observatory_list'),
]
