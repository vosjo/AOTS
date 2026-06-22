from datetime import datetime, timedelta
from itertools import chain

from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.history_helpers import history_actor_for_changelog
from analysis.models import Analysis
from dash.forms import HRDPlotterForm
from dash.plotting import plot_hrd
from dash.starmap_plotting import plot_interactive_starmap
from dash.views import get_modeltype, sort_modified_created, wascreated
from observations.models import LightCurve, Spectrum
from stars.models import Project, Star
from stars.services.starmap import starmap_metadata, starmap_star_records


def _dashboard_project(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request.user.is_anonymous and not project.is_public:
        raise PermissionDenied()
    if not request.user.is_anonymous and not request.user.can_read(project):
        raise PermissionDenied()
    return project


def _recent_changes(project, aware_datetime):
    all_models = []
    for mod in (Star, Spectrum, LightCurve, Analysis):
        all_mod_objs = mod.objects.filter(project=project)
        all_mod_hists = mod.history.filter(project=project)
        most_recent = all_mod_hists.order_by('-history_date')[:25]
        most_recent_ids = most_recent.values_list('id', flat=True)
        all_models.append(all_mod_objs.filter(pk__in=most_recent_ids))

    recent = sorted(chain(*all_models), key=sort_modified_created, reverse=True)[:25]
    entries = []
    for r in recent:
        actor, label = history_actor_for_changelog(r)
        entries.append({
            'modeltype': get_modeltype(r),
            'date': r.history.latest().history_date.isoformat(),
            'user': label,
            'user_pk': actor.pk if actor is not None else None,
            'pk': r.pk,
            'label': str(r),
            'created': wascreated(r),
        })
    return entries


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_bootstrap(request, project_slug):
    project = _dashboard_project(request, project_slug)

    form = HRDPlotterForm(request.GET or None)
    if not form.is_valid():
        form = HRDPlotterForm(initial={
            'nsys': 50, 'xaxis': 'bp_rp', 'yaxis': 'absolute_g_mag', 'size': '', 'color': '',
        })

    parameters = form.get_parameters() if form.is_valid() else {}
    plot_theme = request.query_params.get('theme')
    if parameters:
        figure = plot_hrd(
            request, project.pk,
            parameters['xaxis'], parameters['yaxis'],
            parameters['size'], parameters['color'], parameters['nsys'],
            theme=plot_theme,
        )
    else:
        figure = plot_hrd(request, project.pk, theme=plot_theme)

    dtime_naive = datetime.now() - timedelta(days=7)
    aware_datetime = make_aware(dtime_naive)
    stats = {}
    for mod, modname in zip(
        [Star, Spectrum, LightCurve, Analysis],
        ['nstars', 'nspec', 'nlc', 'nanalyses'],
    ):
        all_mod_objs = mod.objects.filter(project=project)
        stats[modname] = all_mod_objs.count()
        stats[modname + 'lw'] = mod.history.filter(
            project=project, history_date__gte=aware_datetime,
        ).count()

    return Response({
        'project': {'pk': project.pk, 'slug': project.slug, 'name': project.name},
        'stats': stats,
        'recent_changes': _recent_changes(project, aware_datetime),
        'hrd': bokeh_embed_response(figure),
        'hrd_form': {
            'fields': ['nsys', 'xaxis', 'yaxis', 'size', 'color'],
            'labels': {
                name: str(form.fields[name].label).strip()
                for name in ('nsys', 'xaxis', 'yaxis', 'size', 'color')
            },
            'values': parameters or dict(form.initial),
            'choices': {
                name: list(field.choices) for name, field in form.fields.items()
            },
        },
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_starmap(request, project_slug):
    project = _dashboard_project(request, project_slug)
    payload = starmap_metadata(project)

    if request.query_params.get('format') == 'json':
        payload['stars'] = starmap_star_records(project)
        return Response(payload)

    figure = plot_interactive_starmap(project, theme=request.query_params.get('theme'))
    payload['interactive'] = bokeh_embed_response(figure) if figure is not None else None
    return Response(payload)
