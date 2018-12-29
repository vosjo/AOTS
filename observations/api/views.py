 
#from rest_framework.generics import (
   #CreateAPIView,
   #DestroyAPIView,
   #ListAPIView, 
   #UpdateAPIView,
   #RetrieveAPIView,
   #RetrieveUpdateAPIView
#)

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import SpectrumSerializer, SpecFileSerializer, ObservatorySerializer

from observations.models import Spectrum, SpecFile, Observatory

from observations.aux import read_spectrum


# ===============================================================
# Spectrum
# ===============================================================

class SpectrumFilter(filters.FilterSet):
   
   class Meta:
      model = Spectrum
      fields = ['project',]

class SpectrumViewSet(viewsets.ModelViewSet):
   queryset = Spectrum.objects.all()
   serializer_class = SpectrumSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = SpectrumFilter

# ===============================================================
# SpecFile
# ===============================================================

class SpecFileFilter(filters.FilterSet):
   
   class Meta:
      model = SpecFile
      fields = ['project',]

class SpecFileViewSet(viewsets.ModelViewSet):
   queryset = SpecFile.objects.all()
   serializer_class = SpecFileSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = SpecFileFilter



@api_view(['POST'])
def processSpecfile(request, specfile_pk):
   success, message = read_spectrum.process_specfile(specfile_pk)
   specfile = SpecFile.objects.get(pk=specfile_pk)
   
   return Response(SpecFileSerializer(specfile).data)

@api_view(['GET'])
def getSpecfileHeader(request, specfile_pk):
   specfile = SpecFile.objects.get(pk=specfile_pk)
   header = specfile.get_header()
   
   return Response(header)


# ===============================================================
# Observatory
# ===============================================================

class ObservatoryFilter(filters.FilterSet):
   
   name = filters.CharFilter(field_name="name", lookup_expr='icontains')
   
   class Meta:
      model = Observatory
      fields = ['latitude', 'longitude', 'altitude', 'project']


class ObservatoryViewSet(viewsets.ModelViewSet):
   queryset = Observatory.objects.all()
   serializer_class = ObservatorySerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = ObservatoryFilter
   
   
