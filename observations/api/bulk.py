import os

from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from AOTS.permissions_helpers import check_project_access
from AOTS.project_resolution import resolve_project_from_request
from AOTS.task_helpers import run_task
from AOTS.task_status import build_task_status_payload
from AOTS.task_metadata import get_task_owner, user_may_view_task
from observations.auxil import read_lightcurve, read_spectrum
from observations.forms import UploadSpectraDetailForm
from observations.models import LightCurve, Observatory, SpecFile
from observations.services.bulk_download import (
    BULK_DOWNLOAD_KINDS,
    BulkDownloadFile,
    bulk_download_artifact_path,
    bulk_download_filename,
)
from observations.tasks import (
    build_bulk_download_zip_task,
    process_bulk_upload_task,
)
from stars.models import Project
from users.api_auth import APIKeyAuthentication


BULK_AUTH = [SessionAuthentication, APIKeyAuthentication]


def _get_project_from_header(request):
    return resolve_project_from_request(request)


def _parse_star_id_list(request):
    raw = request.META.get('HTTP_STARIDLIST')
    if not raw:
        return None, Response(
            {'detail': 'Missing HTTP_STARIDLIST header.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return [s for s in raw.split(';') if s], None


def _prepare_spec_upload_user_info(request, project):
    upload_form = UploadSpectraDetailForm(request.POST, request.FILES)
    upload_form.fields['observatory'].queryset = Observatory.objects.filter(project=project)
    if not upload_form.is_valid():
        return None, True, Response(
            {'detail': upload_form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_info = read_spectrum.check_form(upload_form.cleaned_data)
    if not user_info.get('add_info'):
        return {}, True, None

    parameters = user_info.keys()
    create_new_star = user_info.get('create_new_star', True)

    if 'observatory' in parameters:
        user_info['obs_pk'] = user_info['observatory'].pk
    elif (
        'observatory_name' in parameters
        and 'observatory_latitude' in parameters
        and 'observatory_longitude' in parameters
        and 'observatory_altitude' in parameters
    ):
        observatory = Observatory(
            project=project,
            name=user_info['observatory_name'],
            latitude=user_info['observatory_latitude'],
            longitude=user_info['observatory_longitude'],
            altitude=user_info['observatory_altitude'],
            space_craft=user_info.get('observatory_is_spacecraft', True),
        )
        observatory.save()
        user_info['obs_pk'] = observatory.pk

    return user_info, create_new_star, None


def _specfile_basename(specfile_pk):
    specfile = SpecFile.objects.filter(pk=specfile_pk).first()
    if specfile and specfile.specfile:
        return specfile.specfile.name.split('/')[-1]
    return ''


def _format_spec_upload_error(exc, specfile_pk=None):
    message = str(exc)
    lower = message.lower()
    filename = _specfile_basename(specfile_pk)
    label = filename or 'The uploaded file'

    if "key 'wavelength'" in lower or (
        'wavelength' in lower and 'does not exist' in lower
    ):
        return (
            f'{label}: unsupported spectrum format — no wavelength column found. '
            'AOTS expects a 1D spectrum file (wavelength and flux).'
        )

    if 'keyword' in lower and 'not found' in lower:
        return (
            f'{label}: incomplete FITS header — {message}. '
            'Enable "Add to / modify header data" and fill in the missing values, '
            'or upload a standard 1D spectrum FITS file.'
        )

    if 'unicodedecodeerror' in lower or 'binary (fits) file' in lower:
        return (
            f'{label}: file could not be read as text. '
            'Upload a valid FITS or plain-text spectrum file.'
        )

    if filename:
        return f'{label}: {message}'
    return message


def _process_uploaded_specfiles(specfile_pks, user_info, create_new_star):
    returned_messages = []
    n_exceptions = 0

    for specfile_pk in specfile_pks:
        try:
            success, message = read_spectrum.process_specfile(
                specfile_pk,
                create_new_star=create_new_star,
                user_info=user_info,
            )
            if success:
                specfile = SpecFile.objects.get(pk=specfile_pk)
                if user_info:
                    _, info_message = read_spectrum.add_userinfo(
                        user_info,
                        specfile.spectrum.pk,
                    )
                    message = f'{message}; {info_message}'
            returned_messages.append(message)
            if not success:
                n_exceptions += 1
        except Exception as exc:
            SpecFile.objects.filter(pk=specfile_pk).delete()
            returned_messages.append(_format_spec_upload_error(exc, specfile_pk))
            n_exceptions += 1

    return returned_messages, n_exceptions


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

    user_info, create_new_star, form_err = _prepare_spec_upload_user_info(request, project)
    if form_err:
        return form_err

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
            label=f'{len(specfile_pks)} specfile(s)',
        )
        return Response(
            {
                'status': 'pending',
                'task_id': task_id,
                'uploaded': len(specfile_pks),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    returned_messages, n_exceptions = _process_uploaded_specfiles(
        specfile_pks,
        user_info,
        create_new_star,
    )

    data = ';'.join(returned_messages)
    if n_exceptions != 0:
        if n_exceptions == len(specfile_pks):
            return Response({'detail': data}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': data}, status=status.HTTP_207_MULTI_STATUS)
    return Response({'detail': data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkUploadLightCurves(request, **kwargs):
    files = request.FILES.getlist('lcfile')
    if not files:
        files = request.FILES.getlist('files')
    if not files:
        return Response(
            {'detail': 'No files uploaded (field lcfile).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project_pk = request.POST.get('project') or request.META.get('HTTP_PROJECTID')
    if project_pk is None:
        return Response(
            {'detail': 'Missing project (form field or HTTP_PROJECTID header).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(pk=int(project_pk))
    except (ValueError, ObjectDoesNotExist):
        return Response(
            {'detail': 'Unknown project.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response(
            {'detail': 'Permission denied for this project.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    returned_messages = []
    n_exceptions = 0

    for f in files:
        newlc = LightCurve(lcfile=f, project=project)
        newlc.save()
        try:
            success, message = read_lightcurve.process_lightcurve(
                newlc.pk,
                create_new_star=True,
            )
            returned_messages.append(message)
            if not success:
                n_exceptions += 1
        except Exception as exc:
            newlc.delete()
            returned_messages.append(f'Exception occured when adding: {f}: {exc}')
            n_exceptions += 1

    data = ';'.join(returned_messages)
    if n_exceptions != 0:
        if n_exceptions == len(files):
            return Response({'detail': data}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': data}, status=status.HTTP_207_MULTI_STATUS)
    return Response({'detail': data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkDownloadStart(request, **kwargs):
    project, err = _get_project_from_header(request)
    if err:
        return err

    requested_ids, err = _parse_star_id_list(request)
    if err:
        return err

    kind = request.query_params.get('kind', 'processed')
    if kind not in BULK_DOWNLOAD_KINDS:
        return Response(
            {'detail': f'Invalid kind. Use one of: {", ".join(sorted(BULK_DOWNLOAD_KINDS))}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        check_project_access(request.user, project)
    except PermissionDenied:
        return Response(
            {'detail': 'Permission denied for this project.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    _, task_id = run_task(
        build_bulk_download_zip_task,
        project.pk,
        requested_ids,
        request.user.pk,
        kind,
        async_requested=True,
        owner_user_id=request.user.pk,
        project_id=project.pk,
        label=f'{kind} ZIP, {len(requested_ids)} star(s)',
    )
    return Response(
        {'status': 'pending', 'task_id': task_id, 'kind': kind},
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
@authentication_classes(BULK_AUTH)
@permission_classes([IsAuthenticated])
def bulkDownloadFile(request, task_id):
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

    download_filename = bulk_download_filename('processed')
    result = AsyncResult(task_id)
    if result.successful() and isinstance(result.result, dict):
        download_filename = result.result.get(
            'download_filename',
            bulk_download_filename(result.result.get('kind', 'processed')),
        )

    return FileResponse(
        BulkDownloadFile(task_id, download_filename=download_filename),
        as_attachment=True,
        filename=download_filename,
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

    return Response(build_task_status_payload(task_id, get_task_owner(task_id)))
