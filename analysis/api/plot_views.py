from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.permissions_helpers import get_object_if_allowed
from rest_framework.exceptions import PermissionDenied
from analysis.auxil import plot_parameters
from analysis.services.analysis_plotting import plot_analysis_detail_figures
from analysis.forms import ParameterPlotterForm
from analysis.models import Analysis
from stars.models import Project


@api_view(['GET'])
@permission_classes([AllowAny])
def parameter_plotter_api(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request.user.is_anonymous and not project.is_public:
        raise PermissionDenied()
    if not request.user.is_anonymous and not request.user.can_read(project):
        raise PermissionDenied()

    form = ParameterPlotterForm(request.GET, project=project) if request.GET else ParameterPlotterForm(project=project)
    if request.GET:
        form.is_valid()
    parameters = form.get_parameters()
    show_regression = request.GET.get('show_regression', '') in ('1', 'true', 'on')

    figure, statistics = plot_parameters.plot_parameters(
        parameters, project=project, show_regression=show_regression,
    )

    return Response({
        'plot': bokeh_embed_response(figure),
        'statistics': statistics,
        'form': {
            'fields': ['xaxis', 'yaxis', 'size', 'color'],
            'labels': {
                name: str(form.fields[name].label).strip()
                for name in ('xaxis', 'yaxis', 'size', 'color')
            },
            'values': {
                **parameters,
                'show_regression': '1' if show_regression else '0',
            },
            'choices': {
                name: [{'value': v, 'label': label} for v, label in field.choices]
                for name, field in form.fields.items()
            },
        },
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def analysis_plots_api(request, pk):
    analysis = get_object_if_allowed(
        Analysis, request, pk, select_related=('project', 'star'),
    )
    all_figs = plot_analysis_detail_figures(analysis)
    return Response(bokeh_embed_response(all_figs))
