
#from django.db.models import Q


#from rest_framework.filters import (
      #SearchFilter,
      #OrderingFilter,
   #)

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer

from stars.models import Project
from analysis.models import Method, DataSet, Parameter
from analysis.aux import process_datasets

#class DatasetListAPIView(ListAPIView):
   #queryset = DataSet.objects.all()
   #serializer_class = DataSetListSerializer

# ===============================================================
# DataSet
# ===============================================================

class DataSetFilter(filters.FilterSet):
   
   class Meta:
      model = DataSet
      fields = ['project',]

class DatasetViewSet(viewsets.ModelViewSet):
   queryset = DataSet.objects.all()
   serializer_class = DataSetListSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = DataSetFilter
   

# ===============================================================
# Methods
# ===============================================================

class MethodFilter(filters.FilterSet):
   
   class Meta:
      model = Method
      fields = ['project',]

class MethodViewSet(viewsets.ModelViewSet):
   queryset = Method.objects.all()
   serializer_class = MethodSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = MethodFilter


# ===============================================================
# Parameter
# ===============================================================

class ParameterFilter(filters.FilterSet):
   
   project = filters.ModelChoiceFilter(queryset=Project.objects.all(),  field_name="star__project", lookup_expr='exact')
   
   class Meta:
      model = Parameter
      fields = ['star',]


class ParameterViewSet(viewsets.ModelViewSet):
   queryset = Parameter.objects.all()
   serializer_class = ParameterListSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = ParameterFilter



@api_view(['POST'])
def processDataSet(request, pk):
   success, message = process_datasets.process_analysis_file(pk)
   dataset = DataSet.objects.get(pk=pk)
   
   return Response(DataSetListSerializer(dataset).data)
