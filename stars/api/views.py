
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    ProjectListSerializer,
    ProjectSerializer,
    StarListSerializer,
    StarSerializer,
    TagListSerializer,
    TagSerializer,
    IdentifierListSerializer,
)

from .filter import (
    StarFilter,
    TagFilter,
)

from stars.models import Project, Star, Identifier, Tag

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user

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

   def list(self, request):
      queryset = Project.objects.all()
      serializer = ProjectListSerializer(queryset, many=True)
      return Response(serializer.data)


# ===============================================================
# STARS
# ===============================================================

class StarViewSet(viewsets.ModelViewSet):
   """
   list:
   Returns a list of all stars/objects in the database
   """

   queryset = Star.objects.all()
   serializer_class = StarSerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = StarFilter

   def get_serializer_class(self):
      if self.action == 'list':
         return StarListSerializer
      if self.action == 'retrieve':
         return StarSerializer
      return StarSerializer


@api_view(['GET'])
def getStarSpecfiles(request, star_pk):
    '''
        Get all SpecFiles associated with a system
    '''

    #   Get system and spectra
    star      = Star.objects.get(pk=star_pk)
    spectra   = star.spectrum_set.all()

    pagination_class = None

    #   Arrange SpecFile infos
    return_dict = {}
    for spectrum in spectra:
        for spec in spectrum.specfile_set.all():
            #return_dict[spec.pk] = "{}@{} - {}".format(
                #spec.hjd,
                #spec.instrument,
                #spec.filetype,
                #)
            return_dict[spec.pk] = "{} - {}".format(
                spec.obs_date,
                spec.instrument,
            )
    return Response(return_dict)


# ===============================================================
# TAGS
# ===============================================================

class TagViewSet(viewsets.ModelViewSet):
   queryset = Tag.objects.all()
   serializer_class = TagSerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = TagFilter


# ===============================================================
# IDENTIFIERS
# ===============================================================

# identifiers doesn't have a special filter, but still only returns the identifiers from allowed projects
# this does require to define a custom get_queryset, which also requires the addition of a basename in the
# router in urls.py

class IdentifierViewSet(viewsets.ModelViewSet):
   #queryset = Identifier.objects.all()
   serializer_class = IdentifierListSerializer

   def list(self, request):
      queryset = Identifier.objects.all()
      star = request.query_params.get('star', None)
      if not star is None:
         queryset = queryset.filter(star=star)
      serializer = IdentifierListSerializer(queryset, many=True)
      return Response(serializer.data)

   def get_queryset(self):
      qs = Identifier.objects.all()
      return get_allowed_objects_to_view_for_user(qs, self.request.user)
