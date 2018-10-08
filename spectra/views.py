from django.shortcuts import get_object_or_404, render, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import Spectrum, SpecFile
from stars.models import Star

from .forms import UploadSpecFileForm


from .aux import read_spectrum

from .plotting import plot_visibility, plot_spectrum

from bokeh.resources import CDN
from bokeh.embed import components

# Create your views here.



def spectra_list(request):
   """
   simplified version of spectra index page using datatables and restframework api
   """
      
   return render(request, 'spectra/spectra_list.html')


def spectra_detail(request, spectrum_id):
   #-- show detailed spectrum information
   
   rebin = 1
   if request.method == 'GET':
      rebin = int(request.GET.get('rebin', 1))
   
   spectrum = get_object_or_404(Spectrum, pk=spectrum_id)
   
   #-- order all spectra
   all_instruments = spectrum.star.spectrum_set.values_list('instrument', flat=True)
   all_spectra = {}
   for inst in set(all_instruments):
      all_spectra[inst] = spectrum.star.spectrum_set.filter(instrument__exact=inst).order_by('hjd')
   
   vis = plot_visibility(spectrum_id)
   spec = plot_spectrum(spectrum_id, rebin=rebin)
   script, div = components({'spec':spec, 'visibility':vis}, CDN)
   
   context = {
      'spectrum': spectrum,
      'all_spectra': all_spectra,
      'figures': div,
      'script': script,
   }
   
   
   return render(request, 'spectra/spectra_detail.html', context)

def specfile_list(request):
   
   upload_form = UploadSpecFileForm()
   
   # Handle file upload
   if request.method == 'POST' and request.user.is_authenticated:
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
               
            return HttpResponseRedirect(reverse('spectra:specfile_list'))
   
   elif request.method != 'GET' and not request.user.is_authenticated:
      messages.add_message(request, messages.ERROR, "You need to login for that action!")
   
   context = {'upload_form': upload_form}
   
   return render(request, 'spectra/specfiles_list.html', context)
