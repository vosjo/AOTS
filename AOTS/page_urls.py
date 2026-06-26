"""Canonical /w/… page URLs for API serializers and embed payloads.

The Vue SPA uses these paths; serializers build hrefs here instead of reverse().
"""


def star_detail_url(project_slug, star_id):
    return f'/w/{project_slug}/systems/stars/{star_id}'


def analysis_detail_url(project_slug, analysis_id):
    return f'/w/{project_slug}/analysis/analyses/{analysis_id}/'


def spectrum_detail_url(project_slug, spectrum_id):
    return f'/w/{project_slug}/observations/spectra/{spectrum_id}/'


def lightcurve_detail_url(project_slug, lightcurve_id):
    return f'/w/{project_slug}/observations/lightcurves/{lightcurve_id}/'


def lightcurve_list_url(project_slug):
    return f'/w/{project_slug}/observations/lightcurves/'
