from bokeh.embed import components
from bokeh.resources import CDN
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, reverse

from AOTS.custom_permissions import check_user_can_view_project
from stars.models import Project
from analysis.auxil import plot_parameters
from analysis.services.analysis_plotting import plot_analysis_detail_figures
from .forms import UploadAnalysisFileForm, ParameterPlotterForm
from .models import Analysis
from .services.analysis_upload import upload_analysis_files


@check_user_can_view_project
def analysis_list(request, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    upload_form = UploadAnalysisFileForm()

    if request.method == 'POST' and request.user.is_authenticated:
        upload_form = UploadAnalysisFileForm(request.POST, request.FILES)
        if upload_form.is_valid():
            files = request.FILES.getlist('datafile')
            message_list = upload_analysis_files(
                project,
                files,
                category=upload_form.cleaned_data.get('category'),
                history_user_id=request.user.pk,
            )

            return JsonResponse(
                {'info': 'Data uploaded', 'messages': message_list},
            )

        return JsonResponse(
            {
                'messages': [
                    [False, '; '.join(
                        f'{field}: {", ".join(errors)}'
                        for field, errors in upload_form.errors.items()
                    ) or 'Invalid upload'],
                ],
            },
            status=400,
        )

    elif request.method == 'POST' and not request.user.is_authenticated:
        return JsonResponse(
            {'messages': [[False, 'You need to login for that action!']]},
            status=403,
        )

    elif request.method != 'GET' and not request.user.is_authenticated:
        messages.add_message(
            request,
            messages.ERROR,
            "You need to login for that action!",
        )

    context = {'upload_form': upload_form,
               'project': project, }

    return render(request, 'analysis/analysis_list.html', context)


@check_user_can_view_project
def analysis_detail(request, analysis_id, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    analysis = get_object_or_404(Analysis, pk=analysis_id)

    related_analyses = analysis.star.analysis_set.all()
    related_stars = Analysis.objects.filter(category=analysis.category).exclude(pk=analysis.pk)

    fit = plot_analysis_detail_figures(analysis)

    histnames = [k for k in fit.keys() if k not in ('fit', 'oc')]
    all_figs = fit
    script, figures = components(all_figs, CDN)

    if not histnames:
        hists = []
    else:
        hists = [figures[name] for name in histnames]

    context = {
        'project': project,
        'analysis': analysis,
        'related_analyses': related_analyses,
        'related_stars': related_stars,
        'fit': figures['fit'],
        'oc': figures['oc'],
        'hist': hists,
        'script': script,
    }

    return render(request, 'analysis/analysis_detail.html', context)


@check_user_can_view_project
def method_list(request, project=None, **kwargs):
    from django.shortcuts import redirect
    return redirect('analysis:analysis_list', project=project)


@check_user_can_view_project
def parameter_plotter(request, project=None, **kwargs):
    project = get_object_or_404(Project, slug=project)

    parameters = {}

    if request.method == 'GET':
        form = ParameterPlotterForm(request.GET, project=project)
        if form.is_valid():
            parameters = form.get_parameters()
    else:
        form = ParameterPlotterForm(project=project)

    figure, statistics = plot_parameters.plot_parameters(parameters, project=project)

    script, figure = components(figure, CDN)

    context = {
        'project': project,
        'figure': figure,
        'script': script,
        'statistics': statistics,
        'form': form,
    }

    return render(request, 'analysis/parameter_plotter.html', context)
