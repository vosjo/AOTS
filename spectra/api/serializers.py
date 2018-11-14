 
from django.urls import reverse
 
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from spectra.models import Spectrum, SpecFile, Observatory
from stars.models import Star
from stars.api.serializers import SimpleStarSerializer

# ===============================================================
# SPECTRA
# ===============================================================

class SpectrumSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   observatory = SerializerMethodField()
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
            'observatory',
            'specfiles',
            'href',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      return SimpleStarSerializer(obj.star).data
      #return Star.objects.get(pk=obj.star).name
      
   def get_observatory(self, obj):
      try:
         return obj.observatory.name
      except:
         return ''
      
   def get_specfiles(self, obj):
      specfiles = SpecFileSerializer(obj.specfile_set, many=True).data
      return specfiles
   
   def get_href(self, obj):
      return reverse('observations:spectra_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.pk})
   

# ===============================================================
# SPECFILE
# ===============================================================

class SpecFileSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   spectrum = SerializerMethodField()
   
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
   
   def get_spectrum(self, obj):
      if obj.spectrum is None:
         return ''
      else:
         return reverse('observations:spectra_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.spectrum.pk})
   

# ===============================================================
# Observatory
# ===============================================================

class ObservatorySerializer(ModelSerializer):
   
   class Meta:
      model = Observatory
      fields = [
            'pk',
            'name',
            'latitude',
            'longitude',
            'altitude',
            'note',
            'url',
            ]
      read_only_fields = ('pk',)
