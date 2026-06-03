from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from AOTS.api_mixins import DatatablesOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.permissions_helpers import get_object_if_allowed
from AOTS.task_helpers import run_task
from analysis.auxil import process_datasets
from analysis.models import Method, DataSet, Parameter
from analysis.tasks import process_dataset_task
from analysis.models import Method, DataSet, Parameter
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
    async_requested = request.query_params.get('async') == '1'
    _, task_id = run_task(
        process_dataset_task,
        pk,
        async_requested=async_requested,
    )
    if task_id:
        return Response(
            {'status': 'pending', 'task_id': task_id},
            status=status.HTTP_202_ACCEPTED,
        )
    dataset.refresh_from_db()

    return Response(DataSetListSerializer(dataset).data)
