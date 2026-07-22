import os
import tempfile

from celery.result import AsyncResult
from django.http import FileResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access
from AOTS.project_resolution import resolve_project_from_request
from AOTS.task_helpers import run_task
from AOTS.task_status import build_task_status_payload
from AOTS.task_metadata import get_task_owner, user_may_view_task
from interop.models import InteropImportBatch
from interop.tasks import export_astra_task, import_astra_task
from users.api_auth import APIKeyAuthentication

AUTH = [SessionAuthentication, APIKeyAuthentication]


def _parse_star_names(request):
    names = request.POST.getlist('star_names') or request.POST.getlist('star_names[]')
    if not names:
        raw = request.POST.get('star_names', '')
        if raw:
            names = [part.strip() for part in raw.split(';') if part.strip()]
    return names


@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def astra_import_api(request):
    project, err = resolve_project_from_request(request)
    if err:
        return err
    check_project_access(request.user, project, require_add=True)

    upload = request.FILES.get('file') or request.FILES.get('package')
    if upload is None:
        return Response({'detail': 'Missing .astra file (field file).'}, status=status.HTTP_400_BAD_REQUEST)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.astra') as tmp:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    star_names = _parse_star_names(request)
    _, task_id = run_task(
        import_astra_task,
        project.pk,
        tmp_path,
        star_names,
        async_requested=True,
        owner_user_id=request.user.pk,
        project_id=project.pk,
        label='ASTRA import',
    )
    return Response({'task_id': task_id}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def astra_import_status_api(request, task_id):
    task_id = str(task_id)
    result = AsyncResult(task_id)
    if not user_may_view_task(request.user, task_id):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    return Response(build_task_status_payload(result))


@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def astra_import_result_api(request, task_id):
    task_id = str(task_id)
    result = AsyncResult(task_id)
    if not user_may_view_task(request.user, task_id):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    if not result.ready():
        return Response({'detail': 'Task not complete.'}, status=status.HTTP_409_CONFLICT)
    if result.failed():
        return Response({'detail': str(result.result)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result.result)


@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def astra_export_api(request):
    project, err = resolve_project_from_request(request)
    if err:
        return err
    check_project_access(request.user, project, require_add=True)

    star_ids = request.POST.getlist('star_ids') or request.data.get('star_ids', [])
    if not star_ids:
        raw = request.POST.get('star_ids', '') or request.data.get('star_ids', '')
        if isinstance(raw, str) and raw:
            star_ids = [int(x) for x in raw.split(';') if x.strip()]
    star_ids = [int(x) for x in star_ids]

    options = {
        'include_spectra': request.data.get('include_spectra', True),
        'include_spectral_fits': request.data.get('include_spectral_fits', True),
        'include_photometry': request.data.get('include_photometry', True),
        'include_lightcurves': request.data.get('include_lightcurves', True),
        'include_sed_models': request.data.get('include_sed_models', True),
        'include_lc_fits': request.data.get('include_lc_fits', True),
        'include_rv': request.data.get('include_rv', True),
        'creator_note': request.data.get('creator_note', ''),
    }
    download_filename = request.data.get('download_filename', '')
    if download_filename:
        options['download_filename'] = download_filename

    _, task_id = run_task(
        export_astra_task,
        project.pk,
        star_ids,
        options,
        async_requested=True,
        owner_user_id=request.user.pk,
        project_id=project.pk,
        label=f'ASTRA export ({len(star_ids)} stars)',
    )
    return Response({'task_id': task_id}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def astra_export_file_api(request, task_id):
    task_id = str(task_id)
    result = AsyncResult(task_id)
    if not user_may_view_task(request.user, task_id):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    if not result.ready() or result.failed():
        return Response({'detail': 'Export not ready.'}, status=status.HTTP_409_CONFLICT)
    payload = result.result or {}
    path = payload.get('file')
    if not path or not os.path.isfile(path):
        return Response({'detail': 'Export file missing.'}, status=status.HTTP_404_NOT_FOUND)
    filename = payload.get('download_filename', 'export.astra')
    return FileResponse(open(path, 'rb'), as_attachment=True, filename=filename)
