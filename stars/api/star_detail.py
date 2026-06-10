from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from AOTS.custom_permissions import IsAllowedOnProject
from AOTS.permissions_helpers import get_object_if_allowed
from observations.api.formatting import format_float_negative_na, hjd2date
from stars.auxil import get_params
from stars.models import Star
from stars.api.serializers import StarSerializer, IdentifierListSerializer


def _param_display(value: str) -> str:
    return (
        value.replace('&pm;', '±')
        .replace('&nbsp;', ' ')
        .strip()
    )


def _related_systems(star):
    grouped = []
    for tag in star.tags.all():
        lower = list(tag.stars.filter(ra__lt=star.ra).order_by('-ra')[:10])
        lower.reverse()
        upper = list(tag.stars.filter(ra__gt=star.ra).order_by('ra')[:10])
        lower_hidden = max(0, tag.stars.filter(ra__lt=star.ra).count() - 10)
        upper_hidden = max(0, tag.stars.filter(ra__gt=star.ra).count() - 10)
        grouped.append({
            'tag': {
                'pk': tag.pk,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
            },
            'stars_lower': [
                {
                    'pk': s.pk,
                    'name': s.name,
                    'observing_status': s.observing_status,
                }
                for s in lower
            ],
            'stars_upper': [
                {
                    'pk': s.pk,
                    'name': s.name,
                    'observing_status': s.observing_status,
                }
                for s in upper
            ],
            'stars_lower_hidden': lower_hidden,
            'stars_upper_hidden': upper_hidden,
        })
    return grouped


def _summary_parameters(star):
    system = [
        {
            'name': name,
            'unit': unit,
            'value': _param_display(value),
        }
        for name, unit, value in star.get_system_summary_parameter()
    ]
    component = [
        {
            'name': name,
            'unit': unit,
            'primary': _param_display(primary),
            'secondary': _param_display(secondary),
        }
        for name, unit, primary, secondary in star.get_component_summary_parameter()
    ]
    return {
        'has_components': len(component) > 0,
        'system': system,
        'component': component,
    }


def _raw_science_rows(star):
    rows = []
    for rawspec in star.rawspecfile_set.filter(filetype='Science').order_by('hjd'):
        rows.append({
            'hjd': rawspec.hjd,
            'hjd_date': hjd2date(rawspec.hjd),
            'instrument': rawspec.instrument,
            'filetype': rawspec.filetype,
            'exptime': rawspec.exptime,
            'linked': False,
        })
    for spectrum in star.spectrum_set.all().order_by('hjd'):
        for spec in spectrum.specfile_set.all().order_by('hjd'):
            for rawspec in spec.rawspecfile_set.filter(filetype='Science').order_by('hjd'):
                rows.append({
                    'hjd': rawspec.hjd,
                    'hjd_date': hjd2date(rawspec.hjd),
                    'instrument': rawspec.instrument,
                    'filetype': rawspec.filetype,
                    'exptime': rawspec.exptime,
                    'linked': True,
                })
    return rows


def _observation_counts(star):
    n_raw = star.rawspecfile_set.filter(filetype='Science').count()
    for spectrum in star.spectrum_set.all():
        for spec in spectrum.specfile_set.all():
            n_raw += spec.rawspecfile_set.filter(filetype='Science').count()
    return {
        'photometry': star.photometry_set.count(),
        'spectra': star.spectrum_set.count(),
        'raw_science': n_raw,
        'lightcurves': star.lightcurve_set.count(),
    }


def build_star_detail_payload(star):
    ra = star.ra
    dec = star.dec
    ra_deg = f'{ra:.4f}' if ra is not None else ''
    dec_deg = f'+{dec:.4f}' if dec is not None and dec >= 0 else f'-{abs(dec):.4f}' if dec is not None else ''

    photometry = [
        {
            'pk': p.pk,
            'band': p.band,
            'value': p.get_value(),
            'error': p.get_error(),
            'measurement': p.measurement,
            'error_value': None if (p.upper_limit or p.lower_limit) else p.error,
            'unit': p.unit,
            'wavelength': p.wavelength,
        }
        for p in star.photometry_set.all()
    ]

    spectra = [
        {
            'pk': spec.pk,
            'hjd': spec.hjd,
            'hjd_date': hjd2date(spec.hjd),
            'instrument': spec.instrument,
            'telescope': spec.telescope,
            'resolution_display': format_float_negative_na(spec.resolution, decimals=0),
            'exptime': spec.exptime,
            'snr_display': format_float_negative_na(spec.snr, decimals=0),
            'minwave_display': format_float_negative_na(spec.minwave, decimals=0),
            'maxwave_display': format_float_negative_na(spec.maxwave, decimals=0),
        }
        for spec in star.spectrum_set.all().order_by('hjd')
    ]

    lightcurves = [
        {
            'pk': lc.pk,
            'hjd': lc.hjd,
            'hjd_date': hjd2date(lc.hjd),
            'passband': lc.passband,
            'exptime': lc.exptime,
            'duration': lc.duration,
        }
        for lc in star.lightcurve_set.all().order_by('hjd')
    ]

    return {
        'star': StarSerializer(star).data,
        'coordinates': {
            'ra_hms': star.ra_hms(),
            'dec_dms': star.dec_dms(),
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
        },
        'related_systems': _related_systems(star),
        'summary_parameters': _summary_parameters(star),
        'observation_counts': _observation_counts(star),
        'photometry': photometry,
        'spectra': spectra,
        'raw_spectra': _raw_science_rows(star),
        'lightcurves': lightcurves,
        'identifiers': IdentifierListSerializer(
            star.identifier_set.all(),
            many=True,
        ).data,
        'stilism_url': (
            f'https://stilism.obspm.fr/reddening?frame=icrs&vlong={ra}&ulong=deg'
            f'&vlat={dec}&ulat=deg'
            if ra is not None and dec is not None else ''
        ),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def star_detail_bootstrap(request, pk):
    star = get_object_or_404(
        Star.objects.select_related('project').prefetch_related(
            'tags',
            'tags__stars',
            'identifier_set',
            'photometry_set',
            'spectrum_set',
            'lightcurve_set',
            'rawspecfile_set',
            'spectrum_set__specfile_set__rawspecfile_set',
        ),
        pk=pk,
    )
    permission = IsAllowedOnProject()
    if not permission.has_object_permission(request, None, star):
        raise PermissionDenied()
    return Response(build_star_detail_payload(star))


@api_view(['GET'])
@permission_classes([AllowAny])
def star_parameters_overview(request, pk):
    get_object_if_allowed(Star, request, pk, select_related=('project',))
    parameters, sources = get_params(pk)
    return Response({
        'sources': [{'pk': s.pk, 'name': s.name} for s in sources],
        'components': [
            {
                'component': comp['component'],
                'rows': [
                    {
                        'name': row['pinfo'].name if row['pinfo'] else '',
                        'unit': row['pinfo'].unit if row['pinfo'] else '',
                        'values': [_param_display(v) for v in row['values']],
                    }
                    for row in comp['params']
                    if row['pinfo'] is not None
                ],
            }
            for comp in parameters
            if comp['params']
        ],
    })
