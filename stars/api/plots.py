from astropy.time import Time
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.permissions_helpers import get_object_if_allowed
from analysis.categories import category_label
from analysis.models import DataSet
from stars.api.star_detail import _param_display
from stars.models import Star
from observations.plotting import plot_sed


def _dataset_parameters(dataset):
    system = [
        {
            'name': name,
            'unit': unit,
            'value': _param_display(value),
        }
        for name, unit, value in dataset.get_system_parameters()
    ]
    component = [
        {
            'name': name,
            'unit': unit,
            'primary': _param_display(primary),
            'secondary': _param_display(secondary),
        }
        for name, unit, primary, secondary in dataset.get_component_parameters()
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
    return Response(bokeh_embed_response(plot_sed(star.pk)))


@api_view(['GET'])
@permission_classes([AllowAny])
def star_dataset_plots(request, pk):
    star = get_object_if_allowed(Star, request, pk, select_related=('project',))
    project = star.project
    plots = []
    datasets = star.dataset_set.select_related('project').order_by('category', 'name')
    for dataset in datasets:
        earliest = dataset.history.earliest()
        plots.append({
            'dataset_id': dataset.pk,
            'dataset_name': dataset.name,
            'category': dataset.category,
            'category_label': category_label(dataset.category),
            'fit': dataset.fit,
            'note': dataset.note,
            'added_by': _history_user_display(earliest.history_user),
            'added_on': Time(earliest.history_date, precision=0).iso,
            'parameters': _dataset_parameters(dataset),
            'detail_href': reverse(
                'analysis:dataset_detail',
                kwargs={'project': project.slug, 'dataset_id': dataset.pk},
            ),
            'embed': bokeh_embed_response(dataset.make_figure()),
        })
    return Response({'plots': plots})
