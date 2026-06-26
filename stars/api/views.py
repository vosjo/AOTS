from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from AOTS.api_mixins import DualOrderingMixin, ProjectFilteredQuerysetMixin
from AOTS.permissions_helpers import get_object_if_allowed
from stars.models import Project, Star, Identifier, Tag
from stars.services import star_io
from .filter import (
    StarFilter,
    TagFilter,
)
from .serializers import (
    ProjectListSerializer,
    ProjectSerializer,
    StarListSerializer,
    StarSerializer,
    TagSerializer,
    IdentifierListSerializer,
)


# ===============================================================
# PROJECTS
# ===============================================================

class ProjectViewSet(viewsets.ModelViewSet):
    """
    list:
    Returns a list of all projects in the database
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = Project.objects.all()
        user = self.request.user
        if user.is_anonymous:
            return qs.filter(is_public=True)
        if user.is_superuser:
            return qs
        return (
            qs.filter(pk__in=user.get_read_projects().values('pk'))
            | qs.filter(is_public=True)
        ).distinct()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = ProjectListSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)


# ===============================================================
# STARS
# ===============================================================

class StarViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    """
    list:
    Returns a list of all stars/objects in the database
    """

    queryset = Star.objects.select_related('project')
    serializer_class = StarSerializer
    default_ordering = ('name',)
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'ra', 'dec', 'classification', 'observing_status']
    allowed_order_fields = frozenset(ordering_fields)

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = StarFilter

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(
            nphot_count=Count('photometry', distinct=True),
            nspec_count=Count('spectrum', distinct=True),
            nlc_count=Count('lightcurve', distinct=True),
        ).prefetch_related('tags', 'analysis_set', 'photometry_set')

    def get_serializer_class(self):
        if self.action == 'list':
            return StarListSerializer
        if self.action == 'retrieve':
            return StarSerializer
        return StarSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'list':
            name_filter = (self.request.query_params.get('name') or '').strip()
            if name_filter:
                context['name_filter'] = name_filter
        return context

    def perform_create(self, serializer):
        star = serializer.save()
        star_io.after_star_saved(star)

    def perform_update(self, serializer):
        star = serializer.save()
        star_io.after_star_saved(star)


@api_view(['GET'])
def getStarSpecfiles(request, star_pk):
    """
        Get all SpecFiles associated with a system
    """
    star = get_object_if_allowed(Star, request, star_pk, select_related=('project',))
    spectra = star.spectrum_set.all()

    return_dict = {}
    for spectrum in spectra:
        for spec in spectrum.specfile_set.all():
            return_dict[spec.pk] = "{} - {}".format(
                spec.obs_date,
                spec.instrument,
            )
    return Response(return_dict)


# ===============================================================
# TAGS
# ===============================================================

class TagViewSet(
    ProjectFilteredQuerysetMixin,
    DualOrderingMixin,
    viewsets.ModelViewSet,
):
    queryset = Tag.objects.select_related('project')
    serializer_class = TagSerializer
    default_ordering = ('name',)
    ordering = ('name',)
    ordering_fields = ['pk', 'name', 'color']

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = TagFilter


# ===============================================================
# IDENTIFIERS
# ===============================================================

# identifiers doesn't have a special filter, but still only returns the identifiers from allowed projects
# this does require to define a custom get_queryset, which also requires the addition of a basename in the
# router in urls.py

class IdentifierViewSet(
    ProjectFilteredQuerysetMixin,
    viewsets.ModelViewSet,
):
    queryset = Identifier.objects.select_related('star', 'star__project')
    serializer_class = IdentifierListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        star = self.request.query_params.get('star')
        if star is not None:
            qs = qs.filter(star=star)
        return qs
