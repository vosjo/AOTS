#import re
#import datetime

from .models import Observatory

from django import forms

#===========================================================================================
#  SPECFILE
#===========================================================================================

class UploadSpectraDetailForm(forms.Form):
   
   spectrumfile = forms.FileField(label='Select a spectrum',
                               widget=forms.ClearableFileInput(attrs={'multiple': True}))
   
   # target
   objectname = forms.CharField(max_length=50, required=False)
   ra = forms.CharField(max_length=15, required=False)
   dec = forms.CharField(max_length=15, required=False)
   
   # Observatory
   observatory = forms.ModelChoiceField(queryset=Observatory.objects.all(), required=False)
   observatory_name = forms.CharField(max_length=100, required=False)
   observatory_latitude = forms.FloatField(required=False)
   observatory_longitude = forms.FloatField(required=False)
   observatory_altitude = forms.FloatField(required=False)
   observatory_is_spacecraft = forms.BooleanField(required=False)
   
   # instrument and setup
   telescope = forms.CharField(max_length=200, required=False)
   instrument = forms.CharField(max_length=200, required=False)
   hjd = forms.FloatField(required=False)
   exptime = forms.FloatField(required=False)
   resolution = forms.FloatField(required=False)
   snr = forms.FloatField(required=False)
   observer = forms.CharField(max_length=50, required=False)
   
   # observing conditions
   wind_speed = forms.FloatField(required=False)
   wind_direction = forms.FloatField(required=False)
   seeing = forms.FloatField(required=False)
   
   # extra
   fluxcal = forms.BooleanField(required=False)
   flux_units = forms.CharField(max_length=50, required=False)
   note = forms.CharField(widget=forms.Textarea(attrs={'cols': 70, 'rows': 10}), required=False)
   create_new_star = forms.BooleanField(required=False)
   merge_spectra_if_possible = forms.BooleanField(required=False)
   
#===========================================================================================
#  SPECFILE
#===========================================================================================


class UploadSpecFileForm(forms.Form):
    specfile = forms.FileField(label='Select a spectrum',
                               widget=forms.ClearableFileInput(attrs={'multiple': True})) 

#===========================================================================================
#  LICHT CURVES
#===========================================================================================

class UploadLightCurveForm(forms.Form):
    lcfile = forms.FileField(label='Select a light curve',
                               widget=forms.ClearableFileInput(attrs={'multiple': True})) 


      
      
