 
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

from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .serializers import StarListSerializer, StarSerializer, TagListSerializer, TagSerializer, IdentifierListSerializer

from stars.models import Star, Identifier, Tag

class StarViewSet(viewsets.ModelViewSet):
   """
   list:
   Returns a list of all stars/objects in the database
   """
   queryset = Star.objects.all()
   serializer_class = StarSerializer
   
   def list(self, request):
      queryset = Star.objects.all()
      serializer = StarListSerializer(queryset, many=True)
      return Response(serializer.data)
      
      
   
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

class TagViewSet(viewsets.ModelViewSet):
   queryset = Tag.objects.all()
   serializer_class = TagSerializer


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
      
   