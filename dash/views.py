from datetime import datetime, timedelta
from bokeh.embed import components
from bokeh.resources import CDN
from django.shortcuts import get_object_or_404, render, reverse
from django.utils.timezone import make_aware

from AOTS.custom_permissions import check_user_can_view_project
from observations.models import Spectrum, LightCurve
from stars.models import Project, Star
from analysis.models import DataSet

from .forms import HRDPlotterForm
from .plotting import plot_hrd
from itertools import chain


def sort_modified_created(model):
    try:
        return model.history.latest().history_date
    except AttributeError:
        return datetime.fromisoformat("19700101")


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

    all_models = []

    for mod, modname in zip([Star, Spectrum, LightCurve, DataSet], ["nstars", "nspec", "nlc", "naly"]):
        all_mod_objs = mod.objects.filter(project=project)
        all_models.append(all_mod_objs)
        stats[modname] = all_mod_objs.count()

        # First history entry must be more recent than seven days ago
        all_mod_objs_lw = mod.history.filter(history_date__gte=aware_datetime, project=project)
        stats[modname + "lw"] = all_mod_objs_lw.count()

    recent_changes = sorted(chain(*all_models), key=sort_modified_created, reverse=True)
    recent_changes = recent_changes[:25]

    recent_changes = [{"modeltype": get_modeltype(r), "date": r.history.latest().history_date, "user": r.history.latest().history_user.username if r.history.latest().history_user is not None else "unknown", "instance": r, "created": wascreated(r)} for r in recent_changes]
    # Possible axes teff, logg, mag, bp_rp
    if len(parameters.keys()) != 0:
        figure = plot_hrd(project.pk, parameters["xaxis"], parameters["yaxis"], parameters["size"], parameters["color"], parameters["nsys"])
        script, div = components(figure, CDN)
    else:
        figure = plot_hrd(project.pk)
        script, div = components(figure, CDN)


    context = {
        'project': project,
        'stats': stats,
        'recent_changes': recent_changes,
        'hrd_plot': div,
        'script': script,
        'form': form
    }

    return render(request, 'dash/dashboard.html', context)