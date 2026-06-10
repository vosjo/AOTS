from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from AOTS.api_mixins import DualOrderingMixin, ProjectFilteredQuerysetMixin
from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
)
from .filter import (
    SpectrumFilter,
    UserInfoFilter,
    SpecFileFilter,
    RawSpecFileFilter,
    LightCurveFilter,
    ObservatoryFilter,
)
from .serializers import (
    SpectrumSerializer,
    SpectrumDetailSerializer,
    SpectrumListSerializer,
    UserInfoSerializer,
    RawSpecFileSerializer,
    SpecFileSerializer,
    SpecFileListSerializer,
    LightCurveSerializer,
    LightCurveDetailSerializer,
    ObservatorySerializer,
)


class SpectrumViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Spectrum.objects.select_related('project', 'star', 'observatory').prefetch_related(
        'specfile_set__rawspecfile_set',
    )
    serializer_class = SpectrumSerializer
    default_ordering = ('hjd',)
    ordering = ('hjd',)
    ordering_fields = [
        'pk', 'hjd', 'instrument', 'resolution', 'airmass', 'exptime',
        'telescope', 'valid', 'fluxcal',
    ]
    allowed_order_fields = frozenset(ordering_fields)

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
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = UserInfo.objects.select_related('project', 'spectrum', 'spectrum__star', 'observatory')
    serializer_class = UserInfoSerializer
    default_ordering = ('hjd',)
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'instrument', 'telescope', 'fluxcal']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = UserInfoFilter


class SpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = SpecFile.objects.select_related('project', 'spectrum', 'spectrum__star')
    serializer_class = SpecFileSerializer
    default_ordering = ('hjd',)
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'instrument', 'filetype', 'exptime', 'resolution']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SpecFileFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return SpecFileListSerializer
        return SpecFileSerializer


class RawSpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = RawSpecFile.objects.select_related('project').prefetch_related(
        'star',
        'specfile',
        'specfile__spectrum',
        'specfile__spectrum__star',
    )
    serializer_class = RawSpecFileSerializer
    default_ordering = ('hjd',)
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'obs_date', 'instrument', 'filetype', 'exptime']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RawSpecFileFilter


class LightCurveViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = LightCurve.objects.select_related('project', 'star', 'observatory')
    serializer_class = LightCurveSerializer
    default_ordering = ('hjd',)
    ordering = ('hjd',)
    ordering_fields = ['pk', 'hjd', 'exptime', 'instrument', 'telescope', 'valid']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = LightCurveFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LightCurveDetailSerializer
        return LightCurveSerializer


class ObservatoryViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Observatory.objects.select_related('project')
    serializer_class = ObservatorySerializer
    default_ordering = ('name',)
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'short_name']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ObservatoryFilter
