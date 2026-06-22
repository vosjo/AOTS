from astropy.time import Time
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.permissions_helpers import get_object_if_allowed
from analysis.categories import category_label
from analysis.parameter_labels import parameter_label_with_unit, unit_display_name
from analysis.services.analysis_display import get_component_parameters, get_system_parameters
from analysis.services.analysis_plotting import plot_analysis_figure
from stars.api.star_detail import _param_display
from stars.models import Star
from observations.plotting import plot_sed


def _analysis_parameters(analysis):
    system = [
        {
            'name': name,
            'display_label': parameter_label_with_unit(name, unit),
            'unit': unit,
            'unit_display': unit_display_name(unit),
            'value': _param_display(value),
        }
        for name, unit, value in get_system_parameters(analysis)
    ]
    component = [
        {
            'name': name,
            'display_label': parameter_label_with_unit(name, unit),
            'unit': unit,
            'unit_display': unit_display_name(unit),
            'primary': _param_display(primary),
            'secondary': _param_display(secondary),
        }
        for name, unit, primary, secondary in get_component_parameters(analysis)
    ]
    return {'system': system, 'component': component}


def _history_user_display(user):
    if user is None:
        return '—'
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return full_name or user.username


@api_view(['GET'])
@permission_classes([AllowAny])
def star_sed_plot(request, pk):
    star = get_object_if_allowed(Star, request, pk, select_related=('project',))
    return Response(bokeh_embed_response(
        plot_sed(star.pk, project=star.project, theme=request.query_params.get('theme')),
    ))


@api_view(['GET'])
@permission_classes([AllowAny])
def star_analysis_plots(request, pk):
    star = get_object_if_allowed(Star, request, pk, select_related=('project',))
    project = star.project
    plot_theme = request.query_params.get('theme')
    plots = []
    analyses = star.analysis_set.select_related('project').order_by('category', 'name')
    for analysis in analyses:
        earliest = analysis.history.earliest()
        plots.append({
            'analysis_id': analysis.pk,
            'analysis_name': analysis.name,
            'category': analysis.category,
            'category_label': category_label(analysis.category),
            'fit': analysis.fit,
            'note': analysis.note,
            'added_by': _history_user_display(earliest.history_user),
            'added_on': Time(earliest.history_date, precision=0).iso,
            'parameters': _analysis_parameters(analysis),
            'detail_href': reverse(
                'analysis:analysis_detail',
                kwargs={'project': project.slug, 'analysis_id': analysis.pk},
            ),
            'embed': bokeh_embed_response(plot_analysis_figure(analysis, theme=plot_theme)),
        })
    return Response({'plots': plots})
