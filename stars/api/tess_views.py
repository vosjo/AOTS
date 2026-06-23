"""REST API for TESS light curve import."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access, get_object_if_allowed
from AOTS.task_helpers import run_task
from observations.services.tess_import import (
    TessImportResult,
    accumulate_tess_bulk_summary,
    import_tess_lightcurves_for_star,
)
from stars.api.gaia_views import _project_from_request, _resolve_star_ids
from stars.models import Star
from stars.tasks import fetch_tess_bulk_task


def _result_payload(result: TessImportResult) -> dict:
    return {
        'status': result.status,
        'detail': result.message,
        'imported': result.imported,
        'skipped_duplicates': result.skipped_duplicates,
        'failed': result.failed,
        'warnings': result.warnings,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def star_fetch_tess_lightcurves(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    result = import_tess_lightcurves_for_star(star)
    if result.status == 'error':
        return Response(_result_payload(result), status=status.HTTP_400_BAD_REQUEST)
    return Response(_result_payload(result))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stars_fetch_tess_bulk(request):
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
            fetch_tess_bulk_task,
            project.pk,
            star_ids,
            request.user.pk,
            async_requested=True,
            owner_user_id=request.user.pk,
            project_id=project.pk,
        )
        return Response(
            {'status': 'pending', 'task_id': task_id, 'total': len(star_ids)},
            status=status.HTTP_202_ACCEPTED,
        )

    summary = {
        'total': len(star_ids),
        'ok': 0,
        'no_match': 0,
        'partial': 0,
        'failed': 0,
        'imported_lightcurves': 0,
        'skipped_duplicates': 0,
        'errors': [],
    }
    for star_pk in star_ids:
        star = Star.objects.get(pk=star_pk, project=project)
        result = import_tess_lightcurves_for_star(star)
        accumulate_tess_bulk_summary(summary, star, result)

    return Response(summary)
