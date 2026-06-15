from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.bokeh_embed import bokeh_embed_response
from AOTS.permissions_helpers import get_object_if_allowed
from observations.models import LightCurve, Spectrum
from observations.plotting import plot_lightcurve, plot_spectrum, plot_visibility


@api_view(['GET'])
@permission_classes([AllowAny])
def spectrum_plot(request, pk):
    spectrum = get_object_if_allowed(
        Spectrum, request, pk, select_related=('project', 'star'),
    )
    parts = {
        p.strip()
        for p in request.GET.get('part', 'spec,visibility').split(',')
        if p.strip()
    }
    figures = {}
    if 'visibility' in parts:
        figures['visibility'] = plot_visibility(spectrum)
    if 'spec' in parts:
        rebin = int(request.GET.get('rebin', 1))
        normalize = request.GET.get('normalize', 'true').lower() != 'false'
        porder = int(request.GET.get('porder', 3))
        figures['spec'] = plot_spectrum(
            pk, rebin=rebin, normalize=normalize, porder=porder, project=spectrum.project,
        )
    return Response(bokeh_embed_response(figures))


@api_view(['GET'])
@permission_classes([AllowAny])
def lightcurve_plot(request, pk):
    lightcurve = get_object_if_allowed(
        LightCurve, request, pk, select_related=('project', 'star'),
    )
    parts = {
        p.strip()
        for p in request.GET.get('part', 'lc_time,lc_phase,visibility').split(',')
        if p.strip()
    }

    period = None
    period_raw = request.GET.get('period')
    if period_raw is not None and period_raw != '':
        try:
            period = float(period_raw) / 24.0
        except (TypeError, ValueError):
            period = None

    binsize = 0.001
    binsize_raw = request.GET.get('binsize', '0.001')
    try:
        binsize = float(binsize_raw)
    except (TypeError, ValueError):
        binsize = 0.001

    figures = {}
    if 'visibility' in parts:
        figures['visibility'] = plot_visibility(lightcurve)
    if 'lc_time' in parts or 'lc_phase' in parts:
        lc_time, lc_phase = plot_lightcurve(
            pk, period=period, binsize=binsize, project=lightcurve.project,
        )
        if 'lc_time' in parts:
            figures['lc_time'] = lc_time
        if 'lc_phase' in parts:
            figures['lc_phase'] = lc_phase
    return Response(bokeh_embed_response(figures))
