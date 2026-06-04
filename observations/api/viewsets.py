from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from AOTS.api_mixins import DatatablesOrderingMixin, ProjectFilteredQuerysetMixin
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
    SpectrumListSerializer,
    UserInfoSerializer,
    RawSpecFileSerializer,
    SpecFileSerializer,
    SpecFileListSerializer,
    LightCurveSerializer,
    ObservatorySerializer,
)


class SpectrumViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Spectrum.objects.select_related('project', 'star', 'observatory').prefetch_related(
        'specfile_set',
    )
    serializer_class = SpectrumSerializer
    default_ordering = ('hjd',)
    allowed_order_fields = frozenset({
        'pk', 'hjd', 'instrument', 'resolution', 'airmass', 'exptime',
        'telescope', 'valid', 'fluxcal',
    })

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SpectrumFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return SpectrumListSerializer
        return SpectrumSerializer


class UserInfoViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = UserInfo.objects.select_related('project', 'spectrum', 'spectrum__star', 'observatory')
    serializer_class = UserInfoSerializer
    default_ordering = ('hjd',)
    allowed_order_fields = frozenset({'pk', 'hjd', 'instrument', 'telescope', 'fluxcal'})

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserInfoFilter


class SpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = SpecFile.objects.select_related('project', 'spectrum', 'spectrum__star')
    serializer_class = SpecFileSerializer
    default_ordering = ('hjd',)
    allowed_order_fields = frozenset({
        'pk', 'hjd', 'instrument', 'filetype', 'exptime', 'resolution',
    })

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SpecFileFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return SpecFileListSerializer
        return SpecFileSerializer


class RawSpecFileViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
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
    allowed_order_fields = frozenset({
        'pk', 'hjd', 'obs_date', 'instrument', 'filetype', 'exptime',
    })

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RawSpecFileFilter


class LightCurveViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = LightCurve.objects.select_related('project', 'star')
    serializer_class = LightCurveSerializer
    default_ordering = ('hjd',)
    allowed_order_fields = frozenset({
        'pk', 'hjd', 'exptime', 'instrument', 'telescope', 'valid',
    })

    filter_backends = (DjangoFilterBackend,)
    filterset_class = LightCurveFilter


class ObservatoryViewSet(
    ProjectFilteredQuerysetMixin,
    DatatablesOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Observatory.objects.select_related('project')
    serializer_class = ObservatorySerializer
    default_ordering = ('name',)
    allowed_order_fields = frozenset({'pk', 'name', 'short_name'})

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ObservatoryFilter
