import os
import shutil
import tempfile

from celery.result import AsyncResult
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
from AOTS.permissions_helpers import check_project_access
from AOTS.task_helpers import run_task
from AOTS.task_metadata import store_task_owner, user_may_view_task
from observations.auxil import read_spectrum
from observations.models import SpecFile, Spectrum
from observations.services.bulk_download import (
    BulkDownloadFile,
    bulk_download_artifact_path,
    build_zip_archive,
    collect_download_files,
    resolve_spectra_queryset,
)
from observations.tasks import (
    build_bulk_spectra_zip_task,
    process_bulk_upload_task,
)
from stars.models import Project
from users.api_auth import APIKeyAuthentication


BULK_AUTH = [SessionAuthentication, APIKeyAuthentication]


def _get_project_from_header(request):
    project_pk = request.META.get('HTTP_PROJECTID')
    if project_pk is None:
        return None, Response(
            {'detail': 'Missing HTTP_PROJECTID header.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(pk=int(project_pk))
    except ValueError:
        try:
            project = Project.objects.get(name__exact=project_pk)
        except ObjectDoesNotExist:
            return None, Response(
                {'detail': 'Unknown project.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ObjectDoesNotExist:
        return None, Response(
            {'detail': 'Unknown project.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return project, None


def _parse_star_id_list(request):
    raw = request.META.get('HTTP_STARIDLIST')
    if not raw:
        return None, Response(
            {'detail': 'Missing HTTP_STARIDLIST header.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return [s for s in raw.split(';') if s], None


@api_view(['POST'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkUploadSpectra(request, **kwargs):
    files = request.FILES.getlist('spectrumfile')
    if not files:
        return Response(
            {'detail': 'No files uploaded (field spectrumfile).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project, err = _get_project_from_header(request)
    if err:
        return err

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response(
            {'detail': 'Permission denied for this project.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    specfile_pks = []
    for f in files:
        newspec = SpecFile(specfile=f, project=project)
        newspec.save()
        specfile_pks.append(newspec.pk)

    if request.query_params.get('async') == '1':
        _, task_id = run_task(
            process_bulk_upload_task,
            project.pk,
            specfile_pks,
            request.user.pk,
            async_requested=True,
            owner_user_id=request.user.pk,
            project_id=project.pk,
        )
        return Response(
            {
                'status': 'pending',
                'task_id': task_id,
                'uploaded': len(specfile_pks),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    user_info = {}
    returned_messages = []
    n_exceptions = 0

    for specfile_pk in specfile_pks:
        try:
            success, message = read_spectrum.process_specfile(
                specfile_pk,
                create_new_star=True,
                user_info=user_info,
            )
            returned_messages.append(message)
            if not success:
                n_exceptions += 1
        except Exception as exc:
            returned_messages.append(str(exc))
            n_exceptions += 1

    data = ';'.join(returned_messages)
    if n_exceptions != 0:
        if n_exceptions == len(specfile_pks):
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_207_MULTI_STATUS)
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkDownloadSpectra(request, **kwargs):
    """
    Synchronous bulk download (legacy).

    Prefer POST /api/observations/bulk-download/start/ (Celery).
    Set query param legacy_sync=1 to use this endpoint explicitly.
    """
    if request.query_params.get('legacy_sync') != '1':
        return Response(
            {
                'detail': (
                    'Synchronous bulk download is deprecated. Use '
                    'POST /api/observations/bulk-download/start/ or pass ?legacy_sync=1.'
                ),
            },
            status=status.HTTP_410_GONE,
        )

    project, err = _get_project_from_header(request)
    if err:
        return err

    requested_stars, err = _parse_star_id_list(request)
    if err:
        return err

    try:
        check_project_access(request.user, project)
    except PermissionDenied:
        return Response(
            {'detail': 'Permission denied for this project.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    spectra = resolve_spectra_queryset(project, requested_stars, request.user)
    files_to_return, preferred_filenames = collect_download_files(spectra)

    if not files_to_return:
        return Response(
            {'detail': 'No files matched the selection.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    zip_path, temp_directory = build_zip_archive(files_to_return, preferred_filenames)
    try:
        with open(zip_path, 'rb') as archive:
            tmp = tempfile.TemporaryFile()
            tmp.write(archive.read())
            tmp.seek(0)
        response = FileResponse(
            tmp,
            as_attachment=True,
            filename='files.zip',
            status=status.HTTP_200_OK,
        )
        response['Deprecation'] = 'true'
        response['Link'] = '</api/observations/bulk-download/start/>; rel="successor-version"'
    finally:
        shutil.rmtree(temp_directory, ignore_errors=True)
    return response


@api_view(['POST'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkDownloadSpectraStart(request, **kwargs):
    project, err = _get_project_from_header(request)
    if err:
        return err

    requested_stars, err = _parse_star_id_list(request)
    if err:
        return err

    try:
        check_project_access(request.user, project)
    except PermissionDenied:
        return Response(
            {'detail': 'Permission denied for this project.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    _, task_id = run_task(
        build_bulk_spectra_zip_task,
        project.pk,
        requested_stars,
        request.user.pk,
        async_requested=True,
        owner_user_id=request.user.pk,
        project_id=project.pk,
    )
    return Response(
        {'status': 'pending', 'task_id': task_id},
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkDownloadSpectraFile(request, task_id):
    if not user_may_view_task(request.user, task_id):
        return Response(
            {'detail': 'Not allowed to access this task.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    path = bulk_download_artifact_path(task_id)
    if not os.path.isfile(path):
        result = AsyncResult(task_id)
        if not result.ready():
            return Response(
                {'detail': 'Download not ready yet.', 'status': result.status},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {'detail': 'Download file not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return FileResponse(
        BulkDownloadFile(task_id),
        as_attachment=True,
        filename='files.zip',
    )


@api_view(['GET'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def getTaskStatus(request, task_id):
    if not user_may_view_task(request.user, task_id):
        return Response(
            {'detail': 'Not allowed to access this task.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    result = AsyncResult(task_id)
    payload = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
    }
    if result.failed():
        payload['error'] = str(result.result)
    elif result.successful():
        payload['result'] = result.result
    return Response(payload)
