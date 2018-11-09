 
#from django.conf.urls import include, url

from django.urls import include, path

from rest_framework import routers

from .views import (
   SpectrumViewSet,
   SpecFileViewSet,
   processSpecfile,
   getSpecfileHeader
   )

app_name = 'observations-api'

router = routers.DefaultRouter()
router.register(r'spectra', SpectrumViewSet)
router.register(r'specfiles', SpecFileViewSet)

#urlpatterns = [
   #url(r'^', include(router.urls)),
   #url(r'^specfiles/(?P<pk>[\w-]+)/process/', processSpecfile, name='process_specfile'),
   #url(r'^specfiles/(?P<pk>[\w-]+)/header/', getSpecfileHeader, name='specfile_header'),
#]

urlpatterns = [
   path('', include(router.urls) ),
   path('specfiles/<int:specfile_pk>/process/', processSpecfile, name='process_specfile'),
   path('specfiles/<int:specfile_pk>/header/', getSpecfileHeader, name='specfile_header'),
]
