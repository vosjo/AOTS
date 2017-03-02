from django import forms

class UploadAnalysisFileForm(forms.Form):
    datafile = forms.FileField(label='Select a file',
                               widget=forms.ClearableFileInput(attrs={'multiple': True})) 
