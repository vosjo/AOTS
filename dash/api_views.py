from datetime import datetime, timedelta
from itertools import chain

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.history_helpers import history_actor_for_changelog
from analysis.models import Analysis
from dash.forms import HRDPlotterForm
from dash.plotting import plot_hrd
from dash.starmap_cache import (
    get_cached_starmap_embed,
    get_starmap_build_task_id,
    set_cached_starmap_embed,
    set_starmap_build_task_id,
)
from dash.changelog import get_modeltype, sort_modified_created, wascreated
from dash.tasks import build_starmap_cache_task
from observations.models import LightCurve, Spectrum
from stars.models import Project, Star
from stars.services.starmap import (
    build_starmap_cache_payload,
    collect_star_positions,
    count_starmap_stars,
    starmap_payload_from_positions,
    starmap_star_records,
)


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


def _build_starmap_embed_sync(project, theme):
    payload = build_starmap_cache_payload(project, theme)
    if payload.get('interactive') is not None:
        set_cached_starmap_embed(project, theme, payload)
    return payload


def _dispatch_starmap_build(project, theme):
    existing_task_id = get_starmap_build_task_id(project, theme)
    if existing_task_id:
        return existing_task_id

    eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    if eager:
        build_starmap_cache_task.apply(args=[project.pk, theme])
        return None

    async_result = build_starmap_cache_task.delay(project.pk, theme)
    set_starmap_build_task_id(project, theme, async_result.id)
    return async_result.id


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
    theme = request.query_params.get('theme')

    if request.query_params.get('format') == 'json':
        all_positions = collect_star_positions(project, for_plot=False)
        payload = starmap_payload_from_positions(all_positions, total_count=len(all_positions))
        payload['stars'] = starmap_star_records(project, positions=all_positions)
        return Response(payload)

    cached_payload = get_cached_starmap_embed(project, theme)
    if cached_payload is not None:
        return Response({**cached_payload, 'status': 'ready'})

    n_stars = count_starmap_stars(project)
    sync_max = getattr(settings, 'STARMAP_SYNC_MAX_STARS', 5_000)
    if n_stars > sync_max:
        _dispatch_starmap_build(project, theme)
        cached_payload = get_cached_starmap_embed(project, theme)
        if cached_payload is not None:
            return Response({**cached_payload, 'status': 'ready'})
        task_id = get_starmap_build_task_id(project, theme)
        return Response(
            {
                'status': 'pending',
                'task_id': task_id,
                'n_stars': 0,
                'n_stars_total': n_stars,
                'n_stars_plotted': 0,
                'downsampled': n_stars > getattr(settings, 'STARMAP_MAX_POINTS', 20_000),
                'colored_by_distance': False,
                'interactive': None,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    payload = _build_starmap_embed_sync(project, theme)
    payload['status'] = 'ready'
    return Response(payload)
