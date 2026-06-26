from datetime import datetime, timedelta


def sort_modified_created(model):
    try:
        return model.history.latest().history_date
    except AttributeError:
        return datetime.fromisoformat('1970-01-01')


def get_modeltype(instance):
    from analysis.models import Analysis
    from observations.models import LightCurve, Spectrum
    from stars.models import Star

    for model, modelname in (
        (Star, 'Star'),
        (Spectrum, 'Spectrum'),
        (LightCurve, 'LightCurve'),
        (Analysis, 'Analysis'),
    ):
        if isinstance(instance, model):
            return modelname
    return None


def wascreated(mod):
    # Modifications within the first 5 minutes of creation count as "created".
    earliest_history = mod.history.earliest()
    latest_history = mod.history.latest()
    return latest_history.history_date - earliest_history.history_date <= timedelta(minutes=5)
