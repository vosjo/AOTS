from django.shortcuts import get_object_or_404, render
from django.contrib import messages

from .aux import process_datasets, plot_parameters

from .models import DataSet
from .forms import UploadAnalysisFileForm

from bokeh.resources import CDN
from bokeh.embed import components

# Create your views here.

def dataset_list(request):
   
   upload_form = UploadAnalysisFileForm()
   
   if request.method == 'POST' and request.user.is_authenticated:
      upload_form = UploadAnalysisFileForm(request.POST, request.FILES)
      if upload_form.is_valid():
         files = request.FILES.getlist('datafile')
         for f in files:
            #-- save the new specfile
            new_dataset = DataSet(datafile=f)
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
            
   elif request.method != 'GET' and not request.user.is_authenticated:
      messages.add_message(request, messages.ERROR, "You need to login for that action!")
   
   
   context = { 'upload_form': upload_form}
   
   return render(request, 'analysis/dataset_list.html', context)


def dataset_detail(request, dataset_id):
   # show details dataset information
   
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
      'dataset': dataset,
      'related_datasets': related_datasets,
      'related_stars': related_stars,
      'fit': figures['fit'],
      'ci': [figures[name] for name in cinames],
      'script': script,
   }
   
   return render(request, 'analysis/dataset_detail.html', context)


def method_list(request):
   
   return render(request, 'analysis/method_list.html')


def parameter_plotter(request):
   
   figure = plot_parameters.plot_parameters('data', 'xpar', 'ypar')
   
   script, figure = components(figure, CDN)
   
   context = {
    'figure' : figure,
    'script' : script,
   }
   
   return render(request, 'analysis/parameter_plotter.html', context)