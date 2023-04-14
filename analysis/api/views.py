from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from analysis.auxil import process_datasets
from analysis.models import Method, DataSet, Parameter
from .filter import DataSetFilter, MethodFilter, ParameterFilter
from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer


# ===============================================================
# DataSet
# ===============================================================

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all()
    serializer_class = DataSetListSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = DataSetFilter


# ===============================================================
# Methods
# ===============================================================

class MethodViewSet(viewsets.ModelViewSet):
    queryset = Method.objects.all()
    serializer_class = MethodSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = MethodFilter


# ===============================================================
# Parameter
# ===============================================================

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
