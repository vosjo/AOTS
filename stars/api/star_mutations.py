import csv
import io

from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access, get_object_if_allowed
from analysis.parameter_labels import parameter_label_with_unit, unit_display_name
from analysis.services import parameter_io
from stars.photometry_bands import (
    ALL_BANDS,
    CSV_MAG_BY_BAND,
    PASSBANDS as passbands,
    survey_groups,
)
from stars.auxil import (
    populate_system,
    resolve_simbad_name,
    update_photometry,
)
from stars.models import Project, Star, Tag
from stars.services import star_io

PHOTNAME_BY_BAND = CSV_MAG_BY_BAND


def _build_photometry_cleaned_data(measurements):
    cleaned = {}
    for entry in measurements:
        band = entry.get('band')
        if band not in PHOTNAME_BY_BAND:
            raise ValueError(f'Unknown photometry band: {band}')
        photname = PHOTNAME_BY_BAND[band]
        value = entry.get('value')
        if value is None:
            cleaned[photname] = None
            continue
        cleaned[photname] = float(value)
        cleaned[photname + 'err'] = float(entry.get('error') or 0)
    return cleaned


def _apply_parameter_updates(star, updates):
    from analysis.models.parameter_source import ParameterSourceKind

    for entry in updates:
        param = star.parameter_set.filter(
            pk=entry['id'],
            average=False,
            parameter_source__kind=ParameterSourceKind.CATALOG,
        ).first()
        if param is None:
            raise ValueError(f'Unknown parameter id: {entry.get("id")}')
        value = entry.get('value')
        if value is None:
            parameter_io.delete_measurement(param)
            continue
        parameter_io.replace_measurement(
            param,
            value=float(value),
            error_l=float(entry.get('error') or 0),
            error_u=float(entry.get('error') or 0),
        )
    return True, 'Parameters updated'


def _editable_parameters(star):
    from analysis.models.parameter_source import ParameterSourceKind

    rows = []
    for param in (
        star.parameter_set
        .filter(
            valid=True,
            average=False,
            parameter_source__kind=ParameterSourceKind.CATALOG,
        )
        .select_related('parameter_source', 'analysis')
        .order_by('component', 'name', 'parameter_source__name')
    ):
        source_name = param.parameter_source.name
        comp_label = param.get_component_display()
        rows.append({
            'id': param.pk,
            'name': param.name,
            'display_label': parameter_label_with_unit(param.cname, param.unit, from_cname=True),
            'component': comp_label,
            'source': source_name,
            'unit': param.unit,
            'unit_display': unit_display_name(param.unit),
            'value': param.value,
            'error': param.error,
            'field_key': f'{param.name}_{comp_label}_{source_name.replace(" ", "-")}',
        })
    return rows


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def star_photometry_options(request, pk):
    get_object_if_allowed(Star, request, pk, select_related=('project',))
    return Response({
        'bands': [
            {'band': band, 'survey': ALL_BANDS[band].survey}
            for band in passbands
        ],
        'surveys': survey_groups(),
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def star_update_photometry(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    measurements = request.data.get('measurements')
    if not isinstance(measurements, list):
        return Response(
            {'detail': 'Expected a list under "measurements".'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        cleaned = _build_photometry_cleaned_data(measurements)
        success, message = update_photometry(cleaned, star.project, star.pk, False)
    except (TypeError, ValueError) as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if not success:
        return Response({'detail': message or 'Update failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': message or 'Photometry updated'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def star_fetch_photometry_vizier(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    from stars.services.vizier_photometry import import_photometry_from_vizier_for_star

    try:
        result = import_photometry_from_vizier_for_star(star)
    except Exception as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if result.status == 'error':
        return Response({'detail': result.message or 'VizieR fetch failed'}, status=status.HTTP_400_BAD_REQUEST)
    if result.status == 'no_match':
        return Response({'detail': result.message or 'No photometry found in VizieR'})
    return Response({'detail': result.message or 'Photometry updated from VizieR'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def star_editable_parameters(request, pk):
    star = get_object_if_allowed(Star, request, pk, select_related=('project',))
    return Response({'parameters': _editable_parameters(star)})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def star_update_parameters(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    updates = request.data.get('updates')
    if not isinstance(updates, list):
        return Response(
            {'detail': 'Expected a list under "updates".'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        success, message = _apply_parameter_updates(star, updates)
    except (TypeError, ValueError) as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if not success:
        return Response({'detail': message or 'Update failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': message or 'Parameters updated'})


def _populate_star_dict(data):
    return {
        'main_id': data['name'],
        'ra': data.get('ra'),
        'dec': data.get('dec'),
        'sp_type': data.get('classification') or '',
        'classification_type': data.get('classification_type') or Star.PHOTOMETRIC,
        'get_simbad': bool(data.get('get_simbad')),
        'parallax': data.get('parallax'),
        'parallax_error': data.get('parallax_error'),
        'pmra_x': data.get('pmra_x'),
        'pmra_error': data.get('pmra_error'),
        'pmdec_x': data.get('pmdec_x'),
        'pmdec_error': data.get('pmdec_error'),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resolve_simbad(request):
    name = (request.query_params.get('name') or '').strip()
    if not name:
        return Response(
            {'detail': 'name is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(resolve_simbad_name(name))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_star_from_form(request):
    project_pk = request.data.get('project')
    name = (request.data.get('name') or '').strip()
    if not project_pk or not name:
        return Response(
            {'detail': 'project and name are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(pk=int(project_pk))
    except (TypeError, ValueError, Project.DoesNotExist):
        return Response({'detail': 'Unknown project.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    sobj = star_io.create_star(name=name, project=project, ra=0.0, dec=0.0)

    star_dict = _populate_star_dict({**request.data, 'name': name})
    tag_ids = request.data.get('tag_ids') or []
    if tag_ids:
        star_dict['tags'] = list(Tag.objects.filter(pk__in=tag_ids, project=project))

    try:
        success, message = populate_system(star_dict, sobj.pk)
    except Exception as exc:
        sobj.delete()
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if not success:
        sobj.delete()
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': message, 'pk': sobj.pk}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_stars(request):
    files = request.FILES.getlist('system')
    if not files:
        return Response(
            {'detail': 'No files uploaded (field system).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project_pk = request.POST.get('project')
    if not project_pk:
        return Response(
            {'detail': 'Missing project.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(pk=int(project_pk))
    except (TypeError, ValueError, Project.DoesNotExist):
        return Response({'detail': 'Unknown project.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    messages = []
    errors = 0
    for uploaded in files:
        if not uploaded.name.lower().endswith('.csv'):
            messages.append(f'{uploaded.name} is not a .csv file')
            errors += 1
            continue
        systems = csv.DictReader(io.TextIOWrapper(uploaded.file, encoding='utf-8-sig'))
        for row in systems:
            main_id = (row.get('main_id') or '').strip()
            if not main_id:
                continue
            sobj = star_io.create_star(name=main_id, project=project, ra=0.0, dec=0.0)
            try:
                success, message = populate_system(row, sobj.pk)
                if success:
                    messages.append(message)
                else:
                    errors += 1
                    messages.append(message)
                    sobj.delete()
            except Exception as exc:
                errors += 1
                sobj.delete()
                messages.append(f'Exception for {main_id}: {exc}')

    data = '; '.join(messages)
    if errors and not messages:
        return Response({'detail': data}, status=status.HTTP_400_BAD_REQUEST)
    if errors:
        return Response({'detail': data}, status=status.HTTP_207_MULTI_STATUS)
    return Response({'detail': data}, status=status.HTTP_200_OK)
