 
from django.conf.urls import include, url
from rest_framework import routers

from .views import (
   SpectrumViewSet,
   SpecFileViewSet,
   processSpecfile,
   getSpecfileHeader
   )

router = routers.DefaultRouter()
router.register(r'spectra', SpectrumViewSet)
router.register(r'specfiles', SpecFileViewSet)

urlpatterns = [
   url(r'^', include(router.urls)),
   url(r'^specfiles/(?P<pk>[\w-]+)/process/', processSpecfile, name='process_specfile'),
   url(r'^specfiles/(?P<pk>[\w-]+)/header/', getSpecfileHeader, name='specfile_header'),
]