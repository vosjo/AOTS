 
#from rest_framework.generics import (
   #CreateAPIView,
   #DestroyAPIView,
   #ListAPIView, 
   #UpdateAPIView,
   #RetrieveAPIView,
   #RetrieveUpdateAPIView
#)

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import SpectrumSerializer, SpecFileSerializer

from spectra.models import Spectrum, SpecFile

from spectra.aux import read_spectrum

class SpectrumViewSet(viewsets.ModelViewSet):
   queryset = Spectrum.objects.all()
   serializer_class = SpectrumSerializer
   
class SpecFileViewSet(viewsets.ModelViewSet):
   queryset = SpecFile.objects.all()
   serializer_class = SpecFileSerializer

@api_view(['POST'])
def processSpecfile(request, pk):
   success, message = read_spectrum.process_specfile(pk)
   specfile = SpecFile.objects.get(pk=pk)
   
   return Response(SpecFileSerializer(specfile).data)

@api_view(['GET'])
def getSpecfileHeader(request, pk):
   specfile = SpecFile.objects.get(pk=pk)
   header = specfile.get_header()
   
   return Response(header)