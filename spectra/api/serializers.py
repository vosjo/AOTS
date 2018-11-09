 
from django.urls import reverse
 
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from spectra.models import Spectrum, SpecFile
from stars.models import Star
from stars.api.serializers import SimpleStarSerializer


class SpectrumSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   specfiles = SerializerMethodField()
   href = SerializerMethodField()
   
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
            'href',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      return SimpleStarSerializer(obj.star).data
      #return Star.objects.get(pk=obj.star).name
      
   def get_specfiles(self, obj):
      specfiles = SpecFileSerializer(obj.specfile_set, many=True).data
      return specfiles
   
   def get_href(self, obj):
      return reverse('observations:spectra_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.pk})

      
class SpecFileSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   
   class Meta:
      model = SpecFile
      fields = [
            'pk',
            'star',
            'spectrum',
            'hjd',
            'instrument',
            'filetype',
            'added_on',
            ]
      read_only_fields = ('pk', 'star')
      
   def get_star(self, obj):
      if obj.spectrum is None:
         return ''
      return obj.spectrum.star.name
