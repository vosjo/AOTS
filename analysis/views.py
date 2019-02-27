from django.shortcuts import get_object_or_404, render, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

from .aux import process_datasets, plot_parameters

from stars.models import Project

from .models import DataSet
from .forms import UploadAnalysisFileForm, ParameterPlotterForm

from bokeh.resources import CDN
from bokeh.embed import components

from AOTS.custom_permissions import check_user_can_view_project



@check_user_can_view_project
def dataset_list(request, project=None,  **kwargs):
   
   project = get_object_or_404(Project, slug=project)
   
   upload_form = UploadAnalysisFileForm()
   
   if request.method == 'POST' and request.user.is_authenticated:
      upload_form = UploadAnalysisFileForm(request.POST, request.FILES)
      if upload_form.is_valid():
         files = request.FILES.getlist('datafile')
         for f in files:
            #-- save the new specfile
            new_dataset = DataSet(datafile=f, project=project, added_by=request.user)
            new_dataset.save()
            
            #-- now process it and add it to a system.
            success, message = process_datasets.process_analysis_file(new_dataset.id)
            message = str(f) + ': ' + message #add name of the file before message
            
            if success:
               level = messages.SUCCESS 
            else:
               level = messages.ERROR
               new_dataset.delete() # delete the dataset if it can't be successfully processed
            
            messages.add_message(request, level, message)
            
         return HttpResponseRedirect(reverse('analysis:dataset_list', kwargs={'project':project.slug}))
            
   elif request.method != 'GET' and not request.user.is_authenticated:
      messages.add_message(request, messages.ERROR, "You need to login for that action!")
   
   
   context = { 'upload_form': upload_form,
               'project': project,}
   
   return render(request, 'analysis/dataset_list.html', context)


@check_user_can_view_project
def dataset_detail(request, dataset_id, project=None,  **kwargs):
   # show details dataset information
   
   project = get_object_or_404(Project, slug=project)
   
   dataset = get_object_or_404(DataSet, pk=dataset_id)
   
   # make related datasets list
   related_datasets = dataset.star.dataset_set.all()
   related_stars = DataSet.objects.filter(method__exact=dataset.method)
   
   # make the main figure
   fit = dataset.make_large_figure()
   
   # make the CI figures if they are available
   ci = dataset.make_parameter_CI_figures()
   
   # create necessary javascript
   cinames = ci.keys()
   ci.update({'fit':fit})
   script, figures = components(ci, CDN)
   
   context = {
      'project': project,
      'dataset': dataset,
      'related_datasets': related_datasets,
      'related_stars': related_stars,
      'fit': figures['fit'],
      'ci': [figures[name] for name in cinames],
      'script': script,
   }
   
   return render(request, 'analysis/dataset_detail.html', context)


@check_user_can_view_project
def method_list(request, project=None,  **kwargs):
   
   project = get_object_or_404(Project, slug=project)
   
   return render(request, 'analysis/method_list.html', {'project': project,})


@check_user_can_view_project
def parameter_plotter(request, project=None,  **kwargs):
   
   project = get_object_or_404(Project, slug=project)
   
   parameters = {}
   
   if request.method == 'GET':
      form = ParameterPlotterForm(request.GET)
      if form.is_valid():
         parameters = form.get_parameters()
   else:
      form = ParameterPlotterForm()
   
   
   figure, statistics = plot_parameters.plot_parameters(parameters)
   
   script, figure = components(figure, CDN)
   
   context = {
    'project': project,
    'figure' : figure,
    'script' : script,
    'statistics' : statistics,
    'form' : form,
   }
   
   return render(request, 'analysis/parameter_plotter.html', context)
