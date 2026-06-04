from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view

from AOTS.api_mixins import DatatablesOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.api_processing import run_process_view
from AOTS.permissions_helpers import get_object_if_allowed
from analysis.models import Method, DataSet, Parameter
from analysis.tasks import process_dataset_task
from .filter import DataSetFilter, MethodFilter, ParameterFilter
from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer


# ===============================================================
# DataSet
# ===============================================================

class DatasetViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = DataSet.objects.select_related('project', 'star', 'method')
    serializer_class = DataSetListSerializer
    default_ordering = ('name',)
    allowed_order_fields = frozenset({'pk', 'name', 'valid'})

    filter_backends = (DjangoFilterBackend,)
    filterset_class = DataSetFilter


# ===============================================================
# Methods
# ===============================================================

class MethodViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Method.objects.select_related('project')
    serializer_class = MethodSerializer
    default_ordering = ('name',)
    allowed_order_fields = frozenset({'pk', 'name', 'slug'})

    filter_backends = (DjangoFilterBackend,)
    filterset_class = MethodFilter


# ===============================================================
# Parameter
# ===============================================================

class ParameterViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = Parameter.objects.select_related('star', 'star__project')
    serializer_class = ParameterListSerializer
    parameter_switch = True

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ParameterFilter


@api_view(['POST'])
def processDataSet(request, pk):
    dataset = get_object_if_allowed(DataSet, request, pk, require_edit=True)
    return run_process_view(
        request, dataset, process_dataset_task, DataSetListSerializer,
    )
