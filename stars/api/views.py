 
#from rest_framework.generics import (
   #CreateAPIView,
   #DestroyAPIView,
   #ListAPIView, 
   #UpdateAPIView,
   #RetrieveAPIView,
   #RetrieveUpdateAPIView
#)

from django.http import JsonResponse
import json

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from django.core.exceptions import ObjectDoesNotExist

from .serializers import ProjectListSerializer, ProjectSerializer, StarListSerializer, StarSerializer, TagListSerializer, TagSerializer, IdentifierListSerializer

from stars.models import Project, Star, Identifier, Tag

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


class StarFilter(filters.FilterSet):
   
   min_ra = filters.NumberFilter(field_name="ra", lookup_expr='gte')
   max_ra = filters.NumberFilter(field_name="ra", lookup_expr='lte')
   
   min_dec = filters.NumberFilter(field_name="dec", lookup_expr='gte')
   max_dec = filters.NumberFilter(field_name="dec", lookup_expr='lte')
   
   classification = filters.CharFilter(field_name="classification", lookup_expr='icontains')
   
   classification_type = filters.MultipleChoiceFilter(field_name="classification_type", choices=Star.CLASSIFICATION_TYPE_CHOICES)
   
   status = filters.MultipleChoiceFilter(field_name="observing_status", choices=Star.OBSERVING_STATUS_CHOICES)
   
   tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())
   
   class Meta:
      model = Star
      fields = ['project',]


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
      
      print ( self.request.__dict__ )
      
      if self.action == 'list':
         return StarListSerializer
      if self.action == 'retrieve':
         return StarSerializer
      return serializers.Default
   
   
#class StarViewSet(viewsets.ModelViewSet):
   #queryset = Star.objects.all()
   #serializer_class = StarListSerializer
   
   ##def list(self, request):
        ##queryset = User.objects.all()
        ##serializer = UserSerializer(queryset, many=True)
        ##return Response(serializer.data)
   
   #def retrieve(self, request, pk=None):
      #star = Star.objects.get(pk=pk)
      #serializer = StarSerializer(star)
      #return Response(serializer.data)
   
   #def update(self, request, pk=None):
      #star = Star.objects.get(pk=pk)
      #serializer = StarSerializer(star)
      #return Response(serializer.data)
   
   #def partial_update(self, request, pk):
      #star = Star.objects.get(pk=pk)
      #serializer = StarSerializer(star, data=request.data, partial=True) # set partial=True to update a data partially
      
      #print request.data
      
      ##if 'tag_set' in request.data:
         ##star.tag_set = request.data['tag_set']
         ##star.save()
         ##print 'new Tags'
      
      #if serializer.is_valid():
         #print serializer.validated_data
         #serializer.save()
         #return JsonResponse(status=201, data=serializer.data)
         
      #return JsonResponse(status=400, data="wrong parameters")


# ===============================================================
# TAGS
# ===============================================================

class TagFilter(filters.FilterSet):
   
   class Meta:
      model = Tag
      fields = ['project',]

class TagViewSet(viewsets.ModelViewSet):
   queryset = Tag.objects.all()
   serializer_class = TagSerializer
   
   filter_backends = (DjangoFilterBackend,)
   filterset_class = TagFilter


# ===============================================================
# IDENTIFIERS
# ===============================================================

   
class IdentifierViewSet(viewsets.ModelViewSet):
   queryset = Identifier.objects.all()
   serializer_class = IdentifierListSerializer
   
   def list(self, request):
      queryset = Identifier.objects.all()
      star = request.query_params.get('star', None)
      if not star is None:
         queryset = queryset.filter(star=star)
      serializer = IdentifierListSerializer(queryset, many=True)
      return Response(serializer.data)
      
   
