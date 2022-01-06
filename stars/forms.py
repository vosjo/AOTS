import re

from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Star, Identifier, Tag

from astropy.coordinates.angles import Angle


class RAField(forms.CharField):
   """
   Custom field to input Right Ascention (RA) in hexadecimal form in hours.
   """
   errormessage = 'Cannot interpret RA angle, try format: hh:mm:ss.ss, hh mm ss.ss or dd.ddddd'

   def clean(self, value):
      if not value:
         return None
      value = value.strip()

      # check if a decimal or hexadecimal number was given
      if re.match('^\d+\.\d+$', value):
         if float(value) > 360 or float(value) < 0:
            raise ValidationError(self.errormessage, code='invalid_ra')
         else:
            return float(value)
      else:
         try:
            return Angle(value.strip(), unit='hour').degree
         except:
            raise ValidationError(self.errormessage, code='invalid_ra')

class DecField(forms.CharField):
   """
   Custom field to input Declination (Dec) in hexadecimal form in hours.
   """

   errormessage = 'Cannot interpret Dec angle, try format: dd:mm:ss.ss, dd mm ss.ss or dd.ddddd'

   def clean(self, value):
      if not value:
         return None

      value = value.strip()

      # check if a decimal or hexadecimal number was given
      if re.match('^\d+\.\d+$', value):
         if float(value) < -90 or float(value) > 90:
            raise ValidationError(self.errormessage, code='invalid_dec')
         else:
            return float(value)
      else:
         try:
            return Angle(value.strip(), unit='degree').degree
         except:
            raise ValidationError(self.errormessage, code='invalid_dec')


# ==================================================================================
# STAR related forms
# ==================================================================================

class RangeField(forms.CharField):
   """
   A char field in which you can specify a range by using the ':' character
   which returns the range as a tuple of floats
   """

   def to_python(self, value):
      """ Normalize the data to a tuple of floats """
      if not value or value=='':
         return None
      if not ':' in value:
         print ('ERR 1')
         raise forms.ValidationError("Please provide a range using ':'.", code='no_range')
      else:
         try:
            value = value.strip().split(':')
            return (float(value[0]), float(value[1]))
         except Exception as e:
            print ('ERR 2')
            raise forms.ValidationError('Cannot interpret provided range', code='invalid_range')


class FilterStarForm(forms.Form):

   ra = RangeField(label="Ra: ", required=False,
              widget=forms.TextInput(attrs={'class':'filter-input', 'placeholder': 'min:max'}))

   dec = RangeField(label="Dec: ", required=False,
               widget=forms.TextInput(attrs={'class':'filter-input', 'placeholder': 'min:max'}))

   mag = RangeField(label="V-mag: ", required=False,
               widget=forms.TextInput(attrs={'class':'filter-input', 'placeholder': 'min:max'}))

   status = forms.MultipleChoiceField(label="Status: ", required=False,
                          widget=forms.CheckboxSelectMultiple)

   classification = forms.MultipleChoiceField(label="Class: ", required=False,
                          widget=forms.CheckboxSelectMultiple)

   tag = forms.MultipleChoiceField(label="Tags: ", required=False,
                          widget=forms.CheckboxSelectMultiple)

   def clean(self):
      cd = self.cleaned_data
      if 'ra' in cd and cd['ra'] == None:
         self.cleaned_data.pop('ra')
      if 'dec' in cd and cd['dec'] == None:
         self.cleaned_data.pop('dec')
      if 'mag' in cd and cd['mag'] == None:
         self.cleaned_data.pop('mag')

      if not 'ra' in self.cleaned_data and not 'dec' in self.cleaned_data and self.cleaned_data['status'] == [] and self.cleaned_data['tag'] == []:
         raise forms.ValidationError("You should at least filter one thing")

      return self.cleaned_data

   def filter_stars(self):
      ra = self.cleaned_data.get('ra', (0,24))
      ra = (ra[0]/24.*360, ra[1]/24.*360) # convert from hours to degrees
      dec = self.cleaned_data.get('dec', (-90,90))

      all_stars = Star.objects.filter(ra__range=ra, dec__range=dec)

      # filter on Status
      if len(self.cleaned_data['status']) > 0:
         stat = self.cleaned_data['status']
         all_stars = all_stars & Star.objects.filter(observing_status__in=stat)

      # filter on Tag
      if len(self.cleaned_data['tag']) > 0:
         tags = self.cleaned_data['tag']
         all_stars = all_stars & Star.objects.filter(tag__pk__in=tags)

      return all_stars.order_by('ra')

class SearchStarForm(forms.Form):
   """
   Form for searching stars on name, classification and tag. The search_stars function
   returns a queryset containing all stars fullfiling the search criterium
   """

   q = forms.CharField(label='Search', required=False,
                      widget=forms.TextInput(attrs={'class':'small-text', 'placeholder': 'Search'}))

   def search(self):
      val = self.cleaned_data['q']
      if val == '':
         return Star.objects.order_by('ra')

      # search on name, class and tag name
      all_stars = Star.objects.filter(Q(name__icontains=val) |
                                      Q(classification__icontains=val) |
                                      Q(tag__name__icontains=val))

      return all_stars.order_by('ra').distinct()


class StarForm(forms.ModelForm):
   """
   https://docs.djangoproject.com/en/1.10/topics/forms/modelforms/
   """

   ra = RAField()
   dec = DecField()

   class Meta:
      model = Star

      fields = ['name', 'ra', 'dec', 'classification', 'classification_type',
                'observing_status']

      widgets = {
               'note': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
         }

   def __init__(self, *args, **kwargs):
        super(StarForm, self).__init__(*args, **kwargs)
        # some fields are not required
        self.fields['classification'].required = False
        self.fields['classification_type'].required = False



