from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from AOTS.api_mixins import ProjectFilteredQuerysetMixin
from observations.models import (
    LightCurve,
    Observatory,
    RawSpecFile,
    SpecFile,
    Spectrum,
    UserInfo,
)

from .filter import (
    LightCurveFilter,
    ObservatoryFilter,
    RawSpecFileFilter,
    SpecFileFilter,
    SpectrumFilter,
    UserInfoFilter,
)
from .serializers import (
    LightCurveDetailSerializer,
    LightCurveSerializer,
    ObservatorySerializer,
    RawSpecFileSerializer,
    SpecFileListSerializer,
    SpecFileSerializer,
    SpectrumDetailSerializer,
    SpectrumListSerializer,
    SpectrumSerializer,
    UserInfoSerializer,
)


class SpectrumViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = Spectrum.objects.select_related('project', 'star', 'observatory').prefetch_related(
        'specfile_set__rawspecfile_set',
    )
    serializer_class = SpectrumSerializer
    ordering = ('hjd',)
    ordering_fields = [
        'pk', 'hjd', 'instrument', 'resolution', 'airmass', 'exptime',
        'telescope', 'valid', 'fluxcal',
    ]

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SpectrumFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return SpectrumListSerializer
        if self.action == 'retrieve':
            return SpectrumDetailSerializer
        return SpectrumSerializer


class UserInfoViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = UserInfo.objects.select_related('project', 'spectrum', 'spectrum__star', 'observatory')
    serializer_class = UserInfoSerializer
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'instrument', 'telescope', 'fluxcal']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = UserInfoFilter


class SpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = SpecFile.objects.select_related('project', 'spectrum', 'spectrum__star')
    serializer_class = SpecFileSerializer
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'instrument', 'filetype', 'exptime', 'resolution']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SpecFileFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return SpecFileListSerializer
        return SpecFileSerializer


class RawSpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = RawSpecFile.objects.select_related('project').prefetch_related(
        'star',
        'specfile',
        'specfile__spectrum',
        'specfile__spectrum__star',
    )
    serializer_class = RawSpecFileSerializer
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'obs_date', 'instrument', 'filetype', 'exptime']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RawSpecFileFilter


class LightCurveViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = LightCurve.objects.select_related('project', 'star', 'observatory')
    serializer_class = LightCurveSerializer
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'exptime', 'instrument', 'telescope', 'valid']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = LightCurveFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LightCurveDetailSerializer
        return LightCurveSerializer


class ObservatoryViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = Observatory.objects.select_related('project')
    serializer_class = ObservatorySerializer
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'short_name']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ObservatoryFilter
