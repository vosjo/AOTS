"""Canonical /w/… page URLs for API serializers and embed payloads.

Legacy Django views and the Vue SPA share the same path layout under /w/.
Serializers must not call reverse() on legacy URL namespaces when AOTS_SPA_CUTOVER
is enabled, because those includes are not registered.
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
