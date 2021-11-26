
#from django.conf.urls import include, url

from django.urls import include, path

from rest_framework import routers

from .views import (
   SpectrumViewSet,
   SpecFileViewSet,
   RawSpecFileViewSet,
   processSpectrum,
   processSpecfile,
   processRawSpecfile,
   getSpecfileHeader,
   LightCurveViewSet,
   processLightCurve,
   getLightCurveHeader,
   ObservatoryViewSet,
   getSpecfilePath,
   )

app_name = 'observations-api'

router = routers.DefaultRouter()
router.register(r'spectra', SpectrumViewSet)
router.register(r'specfiles', SpecFileViewSet)
router.register(r'rawspecfiles', RawSpecFileViewSet)
router.register(r'lightcurves', LightCurveViewSet)
router.register(r'observatories', ObservatoryViewSet)


urlpatterns = [
   path('', include(router.urls) ),
   #    Spectra
   path(
       'spectra/<int:spectrum_pk>/process/',
       processSpectrum,
       name='process_spectrum',
       ),
   #    SpecFiles
   path(
       'specfiles/<int:specfile_pk>/process/',
       processSpecfile,
       name='process_specfile',
       ),
   path(
       'specfiles/<int:specfile_pk>/header/',
       getSpecfileHeader,
       name='specfile_header',
       ),
   path(
       'specfiles/<int:specfile_pk>/path/',
       getSpecfilePath,
       name='specfile_path',
       ),
   #    RawSpecFiles
   path(
       'rawspecfiles/<int:specfile_pk>/process/',
       processRawSpecfile,
       name='process_rawspecfile',
       ),
   #    Lightcurves
   path(
       'lightcurves/<int:lightcurve_pk>/process/',
       processLightCurve,
       name='process_lightcurve',
       ),
   path(
       'lightcurves/<int:lightcurve_pk>/header/',
       getLightCurveHeader,
       name='lightcurve_header',
       ),
]
