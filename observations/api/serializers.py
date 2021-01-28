 
from django.urls import reverse
 
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from observations.models import Spectrum, SpecFile, LightCurve, Observatory
from stars.models import Star
from stars.api.serializers import SimpleStarSerializer

# ===============================================================
# SPECTRA
# ===============================================================

class SpectrumListSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   specfiles = SerializerMethodField()
   href = SerializerMethodField()
   
   class Meta:
      model = Spectrum
      fields = [
            'pk',
            'star',
            'project',
            'hjd',
            'exptime',
            'instrument',
            'telescope',
            'valid',
            'fluxcal',
            'specfiles',
            'href',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      if obj.star is None:
         return ''
      else:
         return SimpleStarSerializer(obj.star).data
      
   def get_specfiles(self, obj):
      specfiles = SimpleSpecFileSerializer(obj.specfile_set, many=True).data
      return specfiles
   
   def get_href(self, obj):
      return reverse('observations:spectrum_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.pk})

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
            'project',
            'hjd',
            'ra',
            'dec',
            'exptime',
            'instrument',
            'telescope',
            'observatory',
            'valid',
            'fluxcal',
            'flux_units',
            'note',
            'specfiles',
            'href',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      if obj.star is None:
         return ''
      else:
         return SimpleStarSerializer(obj.star).data
      #return Star.objects.get(pk=obj.star).name
      
   def get_observatory(self, obj):
      try:
         return obj.observatory.name
      except:
         return ''
      
   def get_specfiles(self, obj):
      specfiles = SimpleSpecFileSerializer(obj.specfile_set, many=True).data
      return specfiles
   
   def get_href(self, obj):
      return reverse('observations:spectrum_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.pk})
   

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
            'filename',
            ]
      read_only_fields = ('pk', 'star')
      
   def get_star(self, obj):
      if obj.spectrum is None or obj.spectrum.star is None:
         return ''
      return obj.spectrum.star.name
   
   def get_spectrum(self, obj):
      if obj.spectrum is None:
         return ''
      else:
         return reverse('observations:spectrum_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.spectrum.pk})
   

class SimpleSpecFileSerializer(ModelSerializer):
   
   class Meta:
      model = SpecFile
      fields = [
            'pk',
            'hjd',
            'instrument',
            'filetype',
            ]
      read_only_fields = ('pk',)

# ===============================================================
# Licht Curves
# ===============================================================

class LightCurveSerializer(ModelSerializer):
   
   star = SerializerMethodField()
   href = SerializerMethodField()
   
   class Meta:
      model = LightCurve
      fields = [
            'pk',
            'star',
            'project',
            'hjd',
            'exptime',
            'cadence',
            'instrument',
            'telescope',
            'valid',
            'href',
            ]
      read_only_fields = ('pk',)
      
   def get_star(self, obj):
      if obj.star is None:
         return ''
      else:
         return SimpleStarSerializer(obj.star).data
   
   def get_href(self, obj):
      return reverse('observations:lightcurve_detail', kwargs={'project':obj.project.slug, 'lightcurve_id':obj.pk})

# ===============================================================
# Observatory
# ===============================================================

class ObservatorySerializer(ModelSerializer):
   
   class Meta:
      model = Observatory
      fields = [
            'pk',
            'project',
            'name',
            'short_name',
            'telescopes', 
            'latitude',
            'longitude',
            'altitude',
            'space_craft',
            'note',
            'url',
            'weatherurl',
            ]
      read_only_fields = ('pk',)
