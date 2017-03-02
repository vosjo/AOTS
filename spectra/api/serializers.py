 
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from spectra.models import Spectrum, SpecFile
from stars.models import Star
from stars.api.serializers import StarSerializer


class SpectrumSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   specfiles = SerializerMethodField()
   
   class Meta:
      model = Spectrum
      fields = [
            'pk',
            'star',
            'hjd',
            'ra',
            'dec',
            'exptime',
            'instrument',
            'telescope',
            'specfiles',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      return StarSerializer(obj.star).data
      #return Star.objects.get(pk=obj.star).name
      
   def get_specfiles(self, obj):
      specfiles = SpecFileSerializer(obj.specfile_set, many=True).data
      return specfiles

      
class SpecFileSerializer(ModelSerializer):
   
   class Meta:
      model = SpecFile
      fields = [
            'pk',
            'spectrum',
            'hjd',
            'instrument',
            'filetype',
            'added_on',
            ]
      read_only_fields = ('pk',)