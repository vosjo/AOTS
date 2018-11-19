
from rest_framework.serializers import ModelSerializer, SerializerMethodField, HyperlinkedRelatedField

from analysis.models import Method, DataSet, Parameter


class MethodSerializer(ModelSerializer):
   
   data_type_display = SerializerMethodField()
   
   class Meta:
      model = Method
      fields = [
            'pk',
            'name',
            'description',
            'slug',
            'color',
            'data_type',
            'data_type_display',
            'derived_parameters',
            'project'
      ]
      read_only_fields = ('pk',)
      
   def get_data_type_display(self, obj):
      return obj.get_data_type_display()

class DataSetListSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   star_pk = SerializerMethodField()
   
   method = SerializerMethodField()
   
   class Meta:
      model = DataSet
      fields = [
            'star',
            'star_pk',
            'pk',
            'name',
            'note',
            'method',
            'valid',
            'added_on',
            'project',
      ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      if obj.star:
         return obj.star.name
      else:
         return ''
   
   def get_star_pk(self, obj):
      if obj.star:
         return obj.star.pk
      else:
         return ''
   
   def get_method(self, obj):
      if obj.method:
         return MethodSerializer(obj.method).data
      else:
         return {}
      
class ParameterListSerializer(ModelSerializer):
   
   class Meta:
      model = Parameter
      fields = [
            'pk',
            'star',
            'name',
            'cname',
            'component',
            'value',
            'error',
            'unit',
            'valid',
      ]
      read_only_fields = ('pk',)
