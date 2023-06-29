import logging
import time
from datetime import datetime, timedelta
from itertools import chain

from bokeh.embed import components
from bokeh.resources import CDN
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import make_aware

from AOTS.custom_permissions import check_user_can_view_project
from analysis.models import DataSet
from observations.models import Spectrum, LightCurve
from stars.models import Project, Star
from .forms import HRDPlotterForm
from .plotting import plot_hrd


def sort_modified_created(model):
    try:
        return model.history.latest().history_date
    except AttributeError:
        return datetime.fromisoformat("1970-01-01")


def get_modeltype(instance):
    for model, modelname in zip([Star, Spectrum, LightCurve, DataSet], ["Star", "Spectrum", "LightCurve", "DataSet"]):
        if isinstance(instance, model):
            return modelname


def wascreated(mod):
    # Modifications within the first 5 minutes of an object being created should not make the object count as having been modified
    earliest_history = mod.history.earliest()
    latest_history = mod.history.latest()

    time_diff = latest_history.history_date - earliest_history.history_date

    if time_diff <= timedelta(minutes=5):
        return True
    else:
        return False


@check_user_can_view_project
def dashboard(request, project=None, **kwargs):
    parameters = {}

    if request.method == 'GET':
        form = HRDPlotterForm(request.GET)
        if form.is_valid():
            parameters = form.get_parameters()
        else:
            form = HRDPlotterForm(initial={'nsys': 50, 'xaxis': 'bp_rp', 'yaxis': "mag", "size": "", "color": ""})
    else:
        form = HRDPlotterForm(initial={'nsys': 50, 'xaxis': 'bp_rp', 'yaxis': "mag", "size": "", "color": ""})

    stats = {}
    project = get_object_or_404(Project, slug=project)

    dtime_naive = datetime.now() - timedelta(days=7)
    aware_datetime = make_aware(dtime_naive)

    start = time.time()

    all_models = []

    # A warning for those who come after me: Do not try to optimize this further, it can only bring you despair.
    for mod, modname in zip([Star, Spectrum, LightCurve, DataSet], ["nstars", "nspec", "nlc", "naly"]):
        all_mod_objs = mod.objects.filter(project=project)
        all_mod_hists = mod.history.filter(project=project)

        most_recent = all_mod_hists.order_by("-history_date")[:25]
        most_recent_ids = most_recent.values_list('id', flat=True)
        most_recent_models = all_mod_objs.filter(pk__in=most_recent_ids)

        all_models.append(most_recent_models)

        stats[modname] = all_mod_objs.count()

        # First history entry must be more recent than seven days ago
        all_mod_objs_lw = all_mod_hists.filter(history_date__gte=aware_datetime)
        stats[modname + "lw"] = all_mod_objs_lw.count()

    recent_changes = sorted(chain(*all_models), key=sort_modified_created, reverse=True)[:25]

    recent_changes = [{"modeltype": get_modeltype(r), "date": r.history.latest().history_date, "user": r.history.latest().history_user if r.history.latest().history_user is not None else "unknown", "instance": r, "created": wascreated(r)} for r in
                      recent_changes]
    # Possible axes teff, logg, mag, bp_rp
    if len(parameters.keys()) != 0:
        figure = plot_hrd(request, project.pk, parameters["xaxis"], parameters["yaxis"], parameters["size"], parameters["color"], parameters["nsys"])
        script, div = components(figure, CDN)
    else:
        figure = plot_hrd(request, project.pk)
        script, div = components(figure, CDN)

    context = {
        'project': project,
        'stats': stats,
        'recent_changes': recent_changes,
        'hrd_plot': div,
        'script': script,
        'form': enumerate(form)
    }

    end = time.time()
    logging.error(f"Time elapsed to generate dash: {end-start}s")

    return render(request, 'dash/dashboard.html', context)
