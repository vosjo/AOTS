from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Star, Tag, Project
from analysis.models import Method, DataSet, DataSource, Parameter
from analysis import models as analModels

from .forms import StarForm

from .plotting import plot_photometry

from bokeh.resources import CDN
from bokeh.embed import components

import json

# Create your views here.

def project_list(request):
   """
   Simplified view of the project page
   """
   
   projects = Project.objects.order_by('name')
   
   context = {'projects': projects}
   
   return render(request, 'stars/project_list.html', context)


def star_list(request, project=None,  **kwargs):
   """
   Simplified version of the index page using datatables and the json api from rest_framework.
   """
   
   project = get_object_or_404(Project, slug=project)
   
   return render(request, 'stars/star_list.html', {'project': project, 'tags': Tag.objects.all()})

   
def tag_list(request, project=None,  **kwargs):
   """
   Simple view showing all defined tags, and allowing for deletion and creation of new ones.
   Tag retrieval, deletion and creation is handled through the API
   """
   
   project = get_object_or_404(Project, slug=project)
   
   return render(request, 'stars/tag_list.html', {'project': project})


def star_detail(request, star_id, project=None, **kwargs):
   """
   Detailed view for star
   interesting for input fields: https://leaverou.github.io/awesomplete/
   and also: https://gist.github.com/conor10/8085ac62fd81ad3002e582d1be65c398
   """
   
   project = get_object_or_404(Project, slug=project)
   
   star = get_object_or_404(Star, pk=star_id)
   context = {
      'star': star,
      'tags' : Tag.objects.all(),
      'project': project,
   }
   
   
   #-- make related systems list
   tags = star.tags.all()
   related_stars = []
   for tag in tags:
      related_stars.append({'tag': tag, 'stars': tag.stars.order_by('ra')})
   
   context['related_stars'] = related_stars
   
   #-- add analysis methods
   methods = Method.objects.all()
   
   datasets, figures = [], []
   for method in methods:
      dataset = star.dataset_set.filter(method__exact = method)
      if dataset:
         dataset = dataset[0]
         figures.append(dataset.make_figure())
         datasets.append(dataset)
   
   if len(figures) > 0:
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
   pSource_pks = star.parameter_set.values_list('data_source').distinct()
   pSource = DataSource.objects.filter(id__in=pSource_pks).order_by('name')
   
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
               p = allParameters.get(name__exact=name, data_source__exact=source.pk)
               values.append(r"{} &pm; {}".format(p.rvalue(), p.rerror()))
               pinfo = p
            except Exception as e:
               values.append("/")
               
         params.append({'values':values, 'pinfo':pinfo})
         
      parameters.append({ 'params': params, 'component':component_names[comp] })
   
   context['allParameters'] = parameters
   context['parameterSources'] = pSource
   
   return render(request, 'stars/star_detail.html', context)

@login_required
def star_edit(request, star_id, project=None, **kwargs):
   """
   View to handle editing of the basic star details
   """
   
   project = get_object_or_404(Project, slug=project)
   
   star = get_object_or_404(Star, pk=star_id)
   
   # if this is a POST request we need to process the form data
   if request.method == 'POST':
      
      if request.POST.get("delete"):
         # Delete this star and return to index
         messages.success(request, "The system: {} was successfully deleted".format(star.name))
         star.delete()
         return redirect('systems:star_list', project.slug)
      
      else:
         # Update the star based on the form
         form = StarForm(request.POST, instance=star)
         
         # check if the input was valid
         if form.is_valid():
            star = form.save()
            
            # redirect details page
            messages.success(request, "This system was successfully updated")
            return redirect('systems:star_detail', project.slug, star.pk)
         
         
   # if a GET (or any other method) create a form for the given star
   else:
      form = StarForm(instance=star)

   return render(request, 'stars/star_edit.html', {'form': form, 'star':star, 'project': project})
