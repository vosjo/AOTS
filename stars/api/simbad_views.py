"""REST API for Simbad identifier import."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import get_object_if_allowed
from stars.models import Star
from stars.services.simbad_identifiers import SimbadIdentifiersResult, sync_simbad_identifiers


def _result_payload(result: SimbadIdentifiersResult) -> dict:
    return {
        'status': result.status,
        'detail': result.message,
        'added': result.added,
        'skipped': result.skipped,
        'total_simbad': result.total_simbad,
        'warnings': result.warnings,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def star_sync_simbad_identifiers(request, pk):
    star = get_object_if_allowed(
        Star, request, pk, select_related=('project',), require_edit=True,
    )
    result = sync_simbad_identifiers(star)
    if result.status != 'ok':
        return Response(_result_payload(result), status=status.HTTP_400_BAD_REQUEST)
    return Response(_result_payload(result))
