import re
import datetime

from django import forms

from .models import Spectrum, SpecFile

#===========================================================================================
#  SPECFILE
#===========================================================================================


class UploadSpecFileForm(forms.Form):
    specfile = forms.FileField(label='Select a spectrum',
                               widget=forms.ClearableFileInput(attrs={'multiple': True})) 

class SearchSpecFileForm(forms.Form):
   """
   Form for searching specfiles
   The default value of the search field is 'unprocessed', showing only the
   specfiles that are not related to a Spectrum object
   """
   
   q = forms.CharField(label='Search', required=False, initial='unprocessed',
                      widget=forms.TextInput(attrs={'class':'small-text', 'placeholder': 'Search'}))
   
   def search(self):
      # force validation
      if not self.is_valid():
         q = 'unprocessed'
      else:
         q = self.cleaned_data['q']
         
         
      if q == 'unprocessed':
         # return specfiles that have no spectrum related to them
         return SpecFile.objects.filter(spectrum__isnull=True)
      elif q == 'recent' or q=='':
         # return specfiles added in the last 7 days
         return SpecFile.objects.filter(added_on__gt=datetime.datetime.today()-
                                     datetime.timedelta(days=7)).order_by('-added_on')
      elif q == 'all':
         return SpecFile.objects.order_by('-added_on')
      

#===========================================================================================
#  SPECTRUM
#===========================================================================================


class SearchSpectrumForm(forms.Form):
   """
   Form for searching spectra on hjd, hjd range, telescope or instrument
   """
   
   q = forms.CharField(label='Search', required=False, 
                      widget=forms.TextInput(attrs={'class':'small-text', 'placeholder': 'Search'}))
   
   def search(self):
      # force validation
      if not self.is_valid():
         return Spectrum.objects.order_by('hjd')
      
      q = self.cleaned_data['q']
      if q == '':
         return Spectrum.objects.order_by('hjd')
      
         # one date as HJD
      m = re.compile("^245\d\d\d\d\.??\d*?$").match(q)
      if m:
         delta = 0.01 if '.' in m.group() else 1
         hjd_q = float(m.group())
         return Spectrum.objects.filter(hjd__lte=hjd_q+delta).filter(hjd__gte=hjd_q-delta)
         
      # two dates as HJD
      m = re.compile("^245\d\d\d\d\.??\d*?\s*?:\s*?245\d\d\d\d\.??\d*?$").match(q)
      if m:
         hjds = m.group().split('-')
         hjd1, hjd2 = float(hjds[0]), float(hjds[1])
         return Spectrum.objects.filter(hjd__lte=hjd2).filter(hjd__gte=hjd1)
      
      # match instrument or telescope
      else:
         return Spectrum.objects.filter(instrument__icontains=q.strip()) | Spectrum.objects.filter(telescope__icontains=q.strip())
      
      
      
#<table class="spectrum-table fullwidth">
#<thead>
   #<tr>
   #<th class="sortcol sortdesc" data-sort="float">HJD</th>
   #<th data-sort="string">Target</th>
   #<th data-sort="string">Instrument</th>
   #<th data-sort="float">Exposure time</th>
   #<th class="nosort"></th>
   #</tr>
#</thead>
#<tbody>
#{% for spec in spectra %}
   #<tr class="spectrum-table-row" id="spectrum-{{spec.pk}}">
   #<th><a href="/spectra/{{ spec.id }}/">{{ spec.hjd }}</a></th>
   #<th><a href="/stars/{{ spec.star.id }}/">{{ spec.star.name }}</a></th>
   #<td>{{ spec.instrument }} @ {{ spec.telescope }}</td>
   #<td>{{ spec.exptime }}</td>
   #<td style="width: 100px"><i class="material-icons button delete" id='delete-spectrum-{{spec.pk}}'>delete</i></td>
   #</tr>
#{% empty %}
   #<tr class="spectrum-table-row" id="no-spectra">
   #<td colspan='5'>No Spectra found.</td>
   #</tr>
#{% endfor %}
#</tbody>
#</table>