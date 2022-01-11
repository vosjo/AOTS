
from django.urls import reverse

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
    )

from stars.models import Star
from stars.api.serializers import SimpleStarSerializer

from astropy.time import Time

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
            'airmass',
            'resolution',
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
            'airmass',
            'resolution',
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


class UserInfoSerializer(ModelSerializer):

    spectrum    = SerializerMethodField()
    observatory = SerializerMethodField()
    #specfiles = SerializerMethodField()
    #href = SerializerMethodField()

    class Meta:
        model = UserInfo
        exclude = ['added_on', 'last_modified', 'added_by']
        #fields = [
            #'pk',
            #'spectrum',
            #'filetype',
            #'objectname',
            #'ra',
            #'dec',
            #'classification',
            #'classification_type',
            #'observatory',
            #'observatory_name',
            #'observatory_latitude',
            #'observatory_longitude',
            #'observatory_altitude',
            #'observatory_is_spacecraft',
            #'telescope',
            #'instrument',
            #'hjd',
            #'exptime',
            #'resolution',
            #'snr',
            #'observer',
            #'wind_speed',
            #'wind_direction',
            #'seeing',
            #'airmass',
            #'normalized',
            #'barycor_bool',
            #'fluxcal',
            #'flux_units',
            #'note',
            #]
        read_only_fields = ('pk',)

    def get_spectrum(self, obj):
        if obj.spectrum is None:
            return ''
        else:
            return obj.spectrum

    def get_observatory(self, obj):
        try:
            return obj.observatory.name
        except:
            return ''

    #def get_specfiles(self, obj):
        #specfiles = SimpleSpecFileSerializer(obj.specfile_set, many=True).data
        #return specfiles

    #def get_href(self, obj):
        #return reverse('observations:spectrum_detail', kwargs={'project':obj.project.slug, 'spectrum_id':obj.pk})


# ===============================================================
# SPECFILE
# ===============================================================

class SpecFileSerializer(ModelSerializer):

    star = SerializerMethodField()
    spectrum = SerializerMethodField()
    added_on = SerializerMethodField()
    filename = SerializerMethodField()

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
        link = reverse(
            'systems:star_detail',
            kwargs={'project':obj.project.slug, 'star_id':obj.spectrum.star.pk},
            )
        return {obj.spectrum.star.name:link}

    def get_spectrum(self, obj):
        if obj.spectrum is None:
            return ''
        return reverse(
            'observations:spectrum_detail',
            kwargs={'project':obj.project.slug, 'spectrum_id':obj.spectrum.pk},
            )

    def get_added_on(self, obj):
        return Time(obj.added_on, precision=0).iso

    def get_filename(self, obj):
        return obj.specfile.name.split('/')[-1]


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
# RAWSPECFILE
# ===============================================================

class RawSpecFileSerializer(ModelSerializer):

    stars     = SerializerMethodField()
    added_on  = SerializerMethodField()
    #specfiles = SerializerMethodField()
    filename  = SerializerMethodField()

    class Meta:
        model = RawSpecFile
        fields = [
                'pk',
                'stars',
                'hjd',
                'instrument',
                'filetype',
                'added_on',
                'filename',
                'exptime',
                #'specfiles',
                ]
        read_only_fields = ('pk', 'stars',)

    def get_stars(self, obj):
        SystemDict = {}
        for sfile in obj.specfile.all():
            SystemDict[sfile.spectrum.star.name] = reverse(
                'systems:star_detail',
                kwargs={
                    'project':sfile.project.slug,
                    'star_id':sfile.spectrum.star.pk,
                    },
                )
        return SystemDict

    def get_added_on(self, obj):
        return Time(obj.added_on, precision=0).iso

    def get_filename(self, obj):
        return obj.rawfile.name.split('/')[-1]


    #def get_specfiles(self, obj):
        #SpecFileList = []
        #for sfile in obj.specfile.all():
            #SpecFileList.append(sfile.hjd)
        #return SpecFileList



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
