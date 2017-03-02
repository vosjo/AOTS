 
from rest_framework.serializers import ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField, SlugRelatedField

from stars.models import Star, Tag, Identifier

# ===============================================================
# TAGS
# ===============================================================
   
      
class TagListSerializer(ModelSerializer):
   
   class Meta:
      model = Tag
      fields = [
            'star',
            'name',
            'description',
            'color',
            'pk',
      ]
      read_only_fields = ('pk',)

class TagSerializer(ModelSerializer):
   
   class Meta:
      model = Tag
      fields = [
            'name',
            'description',
            'color',
            'pk',
      ]
      read_only_fields = ('pk',)


# ===============================================================
# STARS
# ===============================================================

class StarListSerializer(ModelSerializer):
   
   tags = SerializerMethodField()
   vmag = SerializerMethodField()
   classification_type_display = SerializerMethodField()
   observing_status_display = SerializerMethodField()
   
   class Meta:
      model = Star
      fields = [
            'pk',
            'name',
            'ra',
            'dec',
            'ra_hms',
            'dec_dms',
            'classification',
            'classification_type',
            'classification_type_display',
            'observing_status',
            'observing_status_display',
            'note',
            'tags',
            'vmag',
      ]
      read_only_fields = ('pk',)
      
   def get_tags(self, obj):
      tags = TagSerializer(obj.tags, many=True).data
      return tags
   
   def get_vmag(self, obj):
      mag = obj.photometry_set.filter(band__icontains='APASS.V')
      return 0 if len(mag)==0 else mag[0].measurement
   
   def get_classification_type_display(self, obj):
      return obj.get_classification_type_display()
   
   def get_observing_status_display(self, obj):
      return obj.get_observing_status_display()
      

class StarSerializer(ModelSerializer):
   
   tags = SerializerMethodField()
   tag_ids = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        read_only=False,
        source='tags',
    )
   vmag = SerializerMethodField()
   classification_type_display = SerializerMethodField()
   observing_status_display = SerializerMethodField()
   
   class Meta:
      model = Star
      fields = [
            'pk',
            'name',
            'ra',
            'dec',
            'ra_hms',
            'dec_dms',
            'classification',
            'classification_type',
            'classification_type_display',
            'observing_status',
            'observing_status_display',
            'note',
            'tags',
            'tag_ids',
            'vmag',
      ]
      read_only_fields = ('pk', 'tags', 'vmag', 
                          'classification_type_display', 'observing_status_display')
   
   def get_tags(self, obj):
      # this has to be used instead of a through field, as otherwise
      # PUT or PATCH requests fail!
      tags = TagSerializer(obj.tags, many=True).data
      return tags
   
   def get_vmag(self, obj):
      mag = obj.photometry_set.filter(band__icontains='JOHNSON.V')
      return 0 if len(mag)==0 else mag[0].measurement 
      
   def get_classification_type_display(self, obj):
      return obj.get_classification_type_display()
   
   def get_observing_status_display(self, obj):
      return obj.get_observing_status_display()
      

# ===============================================================
# IDENTIFIERS
# ===============================================================
      
class IdentifierListSerializer(ModelSerializer):
   
   class Meta:
      model = Identifier
      fields = [
            'pk',
            'star',
            'name',
      ]
      read_only_fields = ('pk',)