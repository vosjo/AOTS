"""REST API for Gaia DR3 catalog import."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access, get_object_if_allowed
from AOTS.project_resolution import resolve_project_from_request
from AOTS.task_helpers import run_task
from stars.models import Star
from stars.services.gaia_import import GaiaImportResult, import_gaia_dr3_for_star
from stars.tasks import fetch_gaia_bulk_task


def _result_payload(result: GaiaImportResult) -> dict:
    return {
        'status': result.status,
        'detail': result.message,
        'fields_updated': result.fields_updated,
        'warnings': result.warnings,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def star_fetch_gaia_dr3(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    result = import_gaia_dr3_for_star(star)
    if result.status == 'error':
        return Response(_result_payload(result), status=status.HTTP_400_BAD_REQUEST)
    return Response(_result_payload(result))


def _project_from_request(request):
    return resolve_project_from_request(request, body_field='project')


def _resolve_star_ids(project, data) -> tuple[list[int] | None, Response | None]:
    if data.get('all'):
        return list(project.star_set.values_list('pk', flat=True)), None

    star_ids = data.get('star_ids')
    if not isinstance(star_ids, list) or not star_ids:
        return None, Response(
            {'detail': 'Provide star_ids (non-empty list) or all=true.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        ids = [int(pk) for pk in star_ids]
    except (TypeError, ValueError):
        return None, Response(
            {'detail': 'star_ids must be integers.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project_ids = set(
        project.star_set.filter(pk__in=ids).values_list('pk', flat=True),
    )
    if len(project_ids) != len(set(ids)):
        return None, Response(
            {'detail': 'All star_ids must belong to the project.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return ids, None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stars_fetch_gaia_dr3_bulk(request):
    project, err = _project_from_request(request)
    if err:
        return err

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        raise

    star_ids, err = _resolve_star_ids(project, request.data)
    if err:
        return err

    if not star_ids:
        return Response(
            {'detail': 'No stars to process.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    async_requested = request.query_params.get('async', '').lower() in ('1', 'true', 'yes')

    if async_requested:
        _result, task_id = run_task(
            fetch_gaia_bulk_task,
            project.pk,
            star_ids,
            request.user.pk,
            async_requested=True,
            owner_user_id=request.user.pk,
            project_id=project.pk,
            label=f'{len(star_ids)} star(s)',
        )
        return Response(
            {'status': 'pending', 'task_id': task_id, 'total': len(star_ids)},
            status=status.HTTP_202_ACCEPTED,
        )

    results = {
        'total': len(star_ids),
        'ok': 0,
        'no_match': 0,
        'partial': 0,
        'failed': 0,
        'errors': [],
    }
    for star_pk in star_ids:
        star = Star.objects.get(pk=star_pk, project=project)
        result = import_gaia_dr3_for_star(star)
        if result.status == 'error':
            results['failed'] += 1
            results['errors'].append({'star_pk': star_pk, 'message': result.message})
        elif result.status == 'no_match':
            results['no_match'] += 1
        elif result.status == 'partial':
            results['partial'] += 1
        else:
            results['ok'] += 1

    return Response(results)
