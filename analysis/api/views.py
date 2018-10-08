
#from django.db.models import Q


#from rest_framework.filters import (
      #SearchFilter,
      #OrderingFilter,
   #)


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer

from analysis.models import Method, DataSet, Parameter
from analysis.aux import process_datasets

#class DatasetListAPIView(ListAPIView):
   #queryset = DataSet.objects.all()
   #serializer_class = DataSetListSerializer
   
class DatasetViewSet(viewsets.ModelViewSet):
   queryset = DataSet.objects.all()
   serializer_class = DataSetListSerializer
   
   def create(self, request):
        pass

class MethodViewSet(viewsets.ModelViewSet):
   queryset = Method.objects.all()
   serializer_class = MethodSerializer


class ParameterViewSet(viewsets.ModelViewSet):
   queryset = Parameter.objects.all()
   serializer_class = ParameterListSerializer

@api_view(['POST'])
def processDataSet(request, pk):
   success, message = process_datasets.process_analysis_file(pk)
   dataset = DataSet.objects.get(pk=pk)
   
   return Response(DataSetListSerializer(dataset).data)