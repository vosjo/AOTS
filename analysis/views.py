from bokeh.embed import components
from bokeh.resources import CDN
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse

from AOTS.custom_permissions import check_user_can_view_project
from stars.models import Project
from .auxil import process_datasets, plot_parameters
from .forms import UploadAnalysisFileForm, ParameterPlotterForm
from .models import DataSet


@check_user_can_view_project
def dataset_list(request, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    upload_form = UploadAnalysisFileForm()

    if request.method == 'POST' and request.user.is_authenticated:
        upload_form = UploadAnalysisFileForm(request.POST, request.FILES)
        if upload_form.is_valid():
            files = request.FILES.getlist('datafile')
            for f in files:
                # -- save the new specfile
                new_dataset = DataSet(
                    datafile=f,
                    project=project,
                    added_by=request.user,
                )
                new_dataset.save()

                # -- now process it and add it to a system.
                success, message = process_datasets.process_analysis_file(
                    new_dataset.id,
                )
                #   Add name of the file before message
                message = str(f) + ': ' + message

                if success:
                    level = messages.SUCCESS
                else:
                    level = messages.ERROR
                    #   Delete the dataset if it can't be successfully processed
                    new_dataset.delete()

                messages.add_message(request, level, message)

            return HttpResponseRedirect(reverse(
                'analysis:dataset_list',
                kwargs={'project': project.slug}
            ))

    elif request.method != 'GET' and not request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            "You need to login for that action!",
        )

    context = {'upload_form': upload_form,
               'project': project, }

    return render(request, 'analysis/dataset_list.html', context)


@check_user_can_view_project
def dataset_detail(request, dataset_id, project=None, **kwargs):
    # show details dataset information

    project = get_object_or_404(Project, slug=project)

    dataset = get_object_or_404(DataSet, pk=dataset_id)

    # make related datasets list
    related_datasets = dataset.star.dataset_set.all()
    related_stars = DataSet.objects.filter(method__exact=dataset.method)

    # make the main figure
    fit = dataset.make_large_figure()

    oc = dataset.make_OC_figure()

    #   Make the CI figures if they are available
    hist = dataset.make_parameter_hist_figures()

    #   Create necessary javascript
    histnames = hist.keys()
    all_figs = dict(hist, **{'fit': fit, 'oc': oc})
    script, figures = components(all_figs, CDN)

    #   Get only histogram plots
    if not hist:
        hists = []
    else:
        hists = [figures[name] for name in histnames]

    context = {
        'project': project,
        'dataset': dataset,
        'related_datasets': related_datasets,
        'related_stars': related_stars,
        'fit': figures['fit'],
        'oc': figures['oc'],
        'hist': hists,
        'script': script,
    }

    return render(request, 'analysis/dataset_detail.html', context)


@check_user_can_view_project
def method_list(request, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    return render(request, 'analysis/method_list.html', {'project': project, })


@check_user_can_view_project
def parameter_plotter(request, project=None, **kwargs):
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
        'figure': figure,
        'script': script,
        'statistics': statistics,
        'form': form,
    }

    return render(request, 'analysis/parameter_plotter.html', context)
