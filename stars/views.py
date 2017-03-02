from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import HttpResponse, QueryDict, JsonResponse
#from django.template import loader

from .models import Star, Tag
from analysis.models import Method, DataSet, DataSource, Parameter
from analysis import models as analModels

from .forms import StarForm

from .plotting import plot_photometry

from bokeh.resources import CDN
from bokeh.embed import components

import json

# Create your views here.

def star_list(request):
   """
   Simplified version of the index page using datatables and the json api from rest_framework.
   """
   return render(request, 'stars/star_list.html', {'tags' : Tag.objects.all()})

   
def tag_list(request):
   """
   Simple view showing all defined tags, and allowing for deletion and creation of new ones.
   Tag retrieval, deletion and creation is handled through the API
   """
   
   return render(request, 'stars/tag_list.html')


def star_detail(request, star_id):
   """
   Detailed view for star
   interesting for input fields: https://leaverou.github.io/awesomplete/
   and also: https://gist.github.com/conor10/8085ac62fd81ad3002e582d1be65c398
   """
   
   star = get_object_or_404(Star, pk=star_id)
   context = {
      'star': star,
      'tags' : Tag.objects.all(),
   }
   
   
   #-- make navigation list
   all_stars = Star.objects.order_by('ra')
   context['all_stars'] = all_stars
   
   #-- add analysis methods
   methods = Method.objects.all()
   
   datasets, figures = [], []
   for method in methods:
      dataset = star.dataset_set.filter(method__exact = method)
      if dataset:
         dataset = dataset[0]
         figures.append(dataset.make_figure())
         datasets.append(dataset)
   
   #-- Make the bokeh figures and add them to the dataset
   script, div = components(figures, CDN)
   
   datasections = []
   for fig, dataset in zip(div, datasets):
      datasections.append((fig, dataset))
   
   context['datasets'] = datasections
   context['script'] = script
   
   #-- get all parameters for the parameter overview
   
   component_names = {0:'System', 1:'Primary', 2:'Secondary'}
   
   parameters = []
   pSource = star.parameter_set.values_list('data_source').distinct()
   for comp in [analModels.SYSTEM, analModels.PRIMARY, analModels.SECONDARY]:
      pNames = star.parameter_set.filter(component__exact=comp,
                                         valid__exact=True).values_list('name').distinct()
      pNames = sorted([ name[0] for name in pNames], key=analModels.parameter_order)
   
      allParameters = star.parameter_set.all().filter(component__exact=comp)
      
      params = []
      for name in pNames:
         values, pinfo = [], None
         for source in pSource:
            try:
               p = allParameters.get(name__exact=name, data_source__exact=source)
               values.append("{} +- {}".format(p.rvalue(), p.rerror()))
               pinfo = p
            except Exception, e:
               values.append("/")
               
         params.append({'values':values, 'pinfo':pinfo})
         
      parameters.append({ 'params': params, 'component':component_names[comp] })
   
   
   parameterSources = [DataSource.objects.get(pk=pk[0]) for pk in pSource]
   
   context['allParameters'] = parameters
   context['parameterSources'] = parameterSources
   
   return render(request, 'stars/star_detail.html', context)

def star_edit(request, star_id):
   """
   View to handle editing of the basic star details
   """
   
   star = get_object_or_404(Star, pk=star_id)
   
   # if this is a POST request we need to process the form data
   if request.method == 'POST':
      
      if request.POST.get("delete"):
         # Delete this star and return to index
         messages.success(request, "The system: {} was successfully deleted".format(star.name))
         star.delete()
         return redirect('stars:star_list')
      
      else:
         # Update the star based on the form
         form = StarForm(request.POST, instance=star)
         
         # check if the input was valid
         if form.is_valid():
            star = form.save()
            
            # redirect details page
            messages.success(request, "This system was successfully updated")
            return redirect('stars:star_detail', star.pk)
         
         
   # if a GET (or any other method) create a form for the given star
   else:
      form = StarForm(instance=star)

   return render(request, 'stars/star_edit.html', {'form': form, 'star':star})