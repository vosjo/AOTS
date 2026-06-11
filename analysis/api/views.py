from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from AOTS.api_mixins import DualOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.api_processing import run_process_view
from AOTS.permissions_helpers import get_object_if_allowed
from analysis.categories import choices_for_api
from analysis.models import DataSet, Parameter
from analysis.tasks import process_dataset_task
from .filter import DataSetFilter, ParameterFilter
from .serializers import (
    DataSetDetailSerializer,
    DataSetListSerializer,
    ParameterListSerializer,
)


class DatasetViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = DataSet.objects.select_related('project', 'star').prefetch_related(
        'parameter_set',
    )
    serializer_class = DataSetListSerializer
    default_ordering = ('name',)
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'fit', 'category']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = DataSetFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataSetDetailSerializer
        return DataSetListSerializer


class ParameterViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = Parameter.objects.select_related('star', 'star__project')
    serializer_class = ParameterListSerializer
    parameter_switch = True

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ParameterFilter


@api_view(['GET'])
def dataset_categories_api(request):
    return Response({'results': choices_for_api()})


@api_view(['POST'])
def processDataSet(request, pk):
    dataset = get_object_if_allowed(DataSet, request, pk, require_edit=True)
    return run_process_view(
        request, dataset, process_dataset_task, DataSetListSerializer,
    )
