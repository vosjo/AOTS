from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from AOTS.api_mixins import DualOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.api_processing import run_process_view
from AOTS.permissions_helpers import get_object_if_allowed
from analysis.categories import choices_for_api
from analysis.models import Analysis, Parameter
from analysis.tasks import process_analysis_task
from .filter import AnalysisFilter, ParameterFilter
from .serializers import (
    AnalysisDetailSerializer,
    AnalysisListSerializer,
    ParameterListSerializer,
)


class AnalysisViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Analysis.objects.select_related('project', 'star').prefetch_related(
        'parameter_set',
    )
    serializer_class = AnalysisListSerializer
    default_ordering = ('name',)
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'fit', 'category']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = AnalysisFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AnalysisDetailSerializer
        return AnalysisListSerializer


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
def analysis_categories_api(request):
    return Response({'results': choices_for_api()})


@api_view(['POST'])
def processAnalysis(request, pk):
    analysis = get_object_if_allowed(Analysis, request, pk, require_edit=True)
    return run_process_view(
        request, analysis, process_analysis_task, AnalysisListSerializer,
    )
