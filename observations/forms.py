import re
import datetime

from django import forms

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


      
      
