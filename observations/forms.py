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
   objectname = forms.CharField(max_length=50)
   ra = forms.CharField(max_length=15)
   dec = forms.CharField(max_length=15)
   
   # Observatory
   observatory = forms.ModelChoiceField(queryset=Observatory.objects.all())
   observatory_name = forms.CharField(max_length=100)
   observatory_latitude = forms.FloatField()
   observatory_longitude = forms.FloatField()
   observatory_altitude = forms.FloatField()
   observatory_is_spacecraft = forms.BooleanField()
   
   # instrument and setup
   telescope = forms.CharField(max_length=200)
   instrument = forms.CharField(max_length=200)
   hjd = forms.FloatField()
   exptime = forms.FloatField()
   resolution = forms.FloatField()
   snr = forms.FloatField()
   observer = forms.CharField(max_length=50)
   
   # observing conditions
   wind_speed = forms.FloatField()
   wind_direction = forms.FloatField()
   seeing = forms.FloatField()
   
   # extra
   fluxcal = forms.BooleanField()
   flux_units = forms.CharField(max_length=50)
   note = forms.CharField(widget=forms.Textarea(attrs={'cols': 70, 'rows': 10}))
   create_new_star = forms.BooleanField()
   merge_spectra_if_possible = forms.BooleanField()
   
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


      
      
