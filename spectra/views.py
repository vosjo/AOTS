from django.shortcuts import get_object_or_404, render, reverse
from django.http import HttpResponseRedirect, HttpResponse, QueryDict, JsonResponse
from django.contrib import messages

from .models import Spectrum, SpecFile
from stars.models import Star

from .forms import UploadSpecFileForm, SearchSpectrumForm, SearchSpecFileForm

import json


from aux import read_spectrum

from .plotting import plot_visibility, plot_spectrum

from bokeh.resources import CDN
from bokeh.embed import components

# Create your views here.



def spectra_list(request):
   
   context = {
         'search_form': SearchSpectrumForm(),
      }
   
   if request.method == 'GET':
      # Perform a search query 
      search_form = SearchSpectrumForm(request.GET)
      
      context['search_form'] = search_form
      context['spectra'] = search_form.search()
      
      return render(request, 'spectra/spectra_list.html', context)
   
   #elif request.method == 'DELETE':
      #request_body = QueryDict(request.body)
      #response_data = {'success':False}
      
      #if 'delete_spectrum_pk' in request_body:  # DELETE a spectrum
         #spectrum_pk = int(request_body.get('delete_spectrum_pk'))
      
         #Spectrum.objects.filter(pk=spectrum_pk).delete()
         
         #response_data['success'] = True
         #response_data['msg'] = 'The spectrum was deleted.'
      
      #elif 'remove_specfile_pk' in request_body: # REMOVE a specfile
         #specfile_pk = int(request_body.get('remove_specfile_pk'))
         
         #specfile = SpecFile.objects.get(pk = specfile_pk)
         #specfile.spectrum = None
         #specfile.save()
         
         #response_data['success'] = True
         #response_data['msg'] = 'The specfile was removed from the spectrum.'
      
      #elif 'delete_specfile_pk' in request_body: # DELETE a specfile
         #specfile_pk = int(request_body.get('delete_specfile_pk'))
         
         #SpecFile.objects.get(pk = specfile_pk).delete()
         
         #response_data['success'] = True
         #response_data['msg'] = 'The specfile was deleted from the database.'
      
      #return JsonResponse(response_data)
   #else:
      ## not shure when this would actually happen
      #context['spectra'] = Spectrum.objects.order_by('hjd')
      
   #return render(request, 'spectra/spectra_index.html', context)


def spectra_detail(request, spectrum_id):
   #-- show detailed spectrum information
   
   spectrum = get_object_or_404(Spectrum, pk=spectrum_id)
   
   all_stars = Star.objects.order_by('ra')
   
   #-- order all spectra
   all_instruments = spectrum.star.spectrum_set.values_list('instrument', flat=True)
   all_spectra = {}
   for inst in set(all_instruments):
      all_spectra[inst] = spectrum.star.spectrum_set.filter(instrument__exact=inst).order_by('hjd')
   
   vis = plot_visibility(spectrum_id)
   spec = plot_spectrum(spectrum_id)
   script, div = components({'spec':spec, 'visibility':vis}, CDN)
   
   context = {
      'spectrum': spectrum,
      'all_stars': all_stars,
      'all_spectra': all_spectra,
      'figures': div,
      'script': script,
   }
   
   
   return render(request, 'spectra/spectra_detail.html', context)

def specfile_list(request):
   
   upload_form = UploadSpecFileForm()
   
   # Handle file upload
   if request.method == 'POST':
      if 'specfile' in request.FILES:
         upload_form = UploadSpecFileForm(request.POST, request.FILES)
         if upload_form.is_valid():
            
            files = request.FILES.getlist('specfile')
            for f in files:
               #-- save the new specfile
               newspec = SpecFile(specfile=f)
               newspec.save()
               
               #-- now process it and add it to a Spectrum and Object
               success, message = read_spectrum.process_specfile(newspec.pk)
               level = messages.SUCCESS if success else messages.ERROR
               messages.add_message(request, level, message)
               
            return HttpResponseRedirect(reverse('spectra:upload'))
   
   context = {'upload_form': upload_form,}
   
   return render(request, 'spectra/specfiles_list.html', context)
