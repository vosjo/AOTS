"""REST API for VizieR photometry import."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access
from AOTS.task_helpers import run_task
from stars.api.gaia_views import _project_from_request, _resolve_star_ids
from stars.models import Star
from stars.services.vizier_photometry import (
    accumulate_vizier_bulk_summary,
    import_photometry_from_vizier_for_star,
)
from stars.tasks import fetch_vizier_photometry_bulk_task


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stars_fetch_photometry_vizier_bulk(request):
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
            fetch_vizier_photometry_bulk_task,
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

    summary = {
        'total': len(star_ids),
        'ok': 0,
        'no_match': 0,
        'failed': 0,
        'bands_updated_total': 0,
        'errors': [],
    }
    for star_pk in star_ids:
        star = Star.objects.get(pk=star_pk, project=project)
        result = import_photometry_from_vizier_for_star(star)
        accumulate_vizier_bulk_summary(summary, star, result)

    return Response(summary)
