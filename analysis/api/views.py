from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.api_mixins import DualOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.api_processing import run_process_view
from AOTS.permissions_helpers import check_project_access, get_object_if_allowed
from analysis.categories import choices_for_api
from analysis.forms import UploadAnalysisFileForm
from analysis.models import Analysis, Parameter
from analysis.services.analysis_upload import upload_analysis_files
from analysis.tasks import process_analysis_task
from stars.models import Project
from users.api_auth import APIKeyAuthentication
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


UPLOAD_AUTH = [SessionAuthentication, APIKeyAuthentication]


@api_view(['GET'])
def analysis_categories_api(request):
    return Response({'results': choices_for_api()})


@api_view(['POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def upload_analyses_api(request):
    files = request.FILES.getlist('datafile')
    if not files:
        return Response(
            {'messages': [[False, 'No files uploaded (field datafile).']]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project_pk = request.POST.get('project') or request.META.get('HTTP_PROJECTID')
    if project_pk is None:
        return Response(
            {'messages': [[False, 'Missing project (form field or HTTP_PROJECTID header).']]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(pk=int(project_pk))
    except (ValueError, ObjectDoesNotExist):
        return Response(
            {'messages': [[False, 'Unknown project.']]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response(
            {'messages': [[False, 'Permission denied for this project.']]},
            status=status.HTTP_403_FORBIDDEN,
        )

    upload_form = UploadAnalysisFileForm(request.POST, request.FILES)
    if not upload_form.is_valid():
        return Response(
            {
                'messages': [
                    [False, '; '.join(
                        f'{field}: {", ".join(errors)}'
                        for field, errors in upload_form.errors.items()
                    ) or 'Invalid upload'],
                ],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    message_list = upload_analysis_files(project, files)
    return Response({'info': 'Data uploaded', 'messages': message_list})


@api_view(['POST'])
def processAnalysis(request, pk):
    analysis = get_object_if_allowed(Analysis, request, pk, require_edit=True)
    return run_process_view(
        request, analysis, process_analysis_task, AnalysisListSerializer,
    )
