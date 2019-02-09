 
#from django.conf.urls import include, url

from django.urls import include, path

from rest_framework import routers

from .views import (
   SpectrumViewSet,
   SpecFileViewSet,
   processSpecfile,
   getSpecfileHeader,
   LightCurveViewSet,
   processLightCurve,
   getLightCurveHeader,
   ObservatoryViewSet,
   )

app_name = 'observations-api'

router = routers.DefaultRouter()
router.register(r'spectra', SpectrumViewSet)
router.register(r'specfiles', SpecFileViewSet)
router.register(r'lightcurves', LightCurveViewSet)
router.register(r'observatories', ObservatoryViewSet)


urlpatterns = [
   path('', include(router.urls) ),
   path('specfiles/<int:specfile_pk>/process/', processSpecfile, name='process_specfile'),
   path('specfiles/<int:specfile_pk>/header/', getSpecfileHeader, name='specfile_header'),
   path('lightcurves/<int:lightcurve_pk>/process/', processLightCurve, name='process_lightcurve'),
   path('lightcurves/<int:lightcurve_pk>/header/', getLightCurveHeader, name='lightcurve_header'),
]
