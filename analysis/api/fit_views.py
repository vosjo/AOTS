"""Multi-contributor fit API endpoints."""

from __future__ import annotations

import os
import tempfile

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analysis.models import Analysis
from analysis.services.fit_contribution import (
    FitContributionError,
    contribute_fit,
    delete_fit_record,
    fit_parameters_for_api,
    patch_fit_metadata,
    set_container_best_fit,
)
from analysis.services.fit_permissions import (
    category_supports_multi_fit,
    user_can_delete_fit,
    user_can_edit_fit,
)
from analysis.services.fit_sync import sync_fits_from_hdf5
from AOTS.permissions_helpers import check_project_access
from users.api_auth import APIKeyAuthentication

UPLOAD_AUTH = [SessionAuthentication, APIKeyAuthentication]


def _load_analysis(request, pk):
    analysis = get_object_or_404(Analysis.objects.select_related('project'), pk=pk)
    check_project_access(request.user, analysis.project, require_add=False)
    return analysis


def _serialize_fit(fit, *, user) -> dict:
    uploaded_by = None
    if fit.uploaded_by_id:
        uploaded_by = {
            'pk': fit.uploaded_by_id,
            'username': fit.uploaded_by.get_username() if fit.uploaded_by else '',
        }
    return {
        'id': fit.fit_id,
        'label': fit.label,
        'method': fit.method,
        'is_best_fit': fit.is_best_fit,
        'external_id': fit.external_id,
        'uploaded_by': uploaded_by,
        'uploaded_on': fit.created.isoformat() if fit.created else '',
        'can_edit': user_can_edit_fit(user, fit),
        'can_delete': user_can_delete_fit(user, fit),
    }


def _fits_list(analysis: Analysis, user) -> list[dict]:
    sync_fits_from_hdf5(analysis)
    return [_serialize_fit(f, user=user) for f in analysis.fits.all()]


@api_view(['GET', 'POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def analysis_fits_api(request, pk):
    analysis = _load_analysis(request, pk)
    if not category_supports_multi_fit(analysis.category):
        return Response({'detail': 'Analysis category does not support multi-fit.'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        return Response({'results': _fits_list(analysis, request.user)})

    upload = request.FILES.get('datafile') or request.FILES.get('file')
    if not upload:
        return Response({'detail': 'Missing fit file (datafile).'}, status=status.HTTP_400_BAD_REQUEST)

    suffix = os.path.splitext(upload.name)[1] or '.h5'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        fit_id = contribute_fit(
            analysis,
            request.user,
            upload_path=tmp_path,
            label=(request.POST.get('label') or '').strip(),
            method=(request.POST.get('method') or '').strip(),
            external_id=(request.POST.get('external_id') or '').strip(),
            set_as_best=request.POST.get('set_as_best', '').lower() in ('1', 'true', 'yes'),
        )
    except FitContributionError as exc:
        return Response({'detail': str(exc)}, status=exc.status_code)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return Response({'fit_id': fit_id, 'fits': _fits_list(analysis, request.user)}, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def analysis_fit_detail_api(request, pk, fit_id):
    analysis = _load_analysis(request, pk)
    if request.method == 'DELETE':
        try:
            delete_fit_record(analysis, fit_id, request.user)
        except FitContributionError as exc:
            return Response({'detail': str(exc)}, status=exc.status_code)
        return Response({'fits': _fits_list(analysis, request.user)})

    label = request.data.get('label')
    method = request.data.get('method')
    try:
        patch_fit_metadata(analysis, fit_id, request.user, label=label, method=method)
    except FitContributionError as exc:
        return Response({'detail': str(exc)}, status=exc.status_code)
    return Response({'fits': _fits_list(analysis, request.user)})


@api_view(['POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def analysis_best_fit_api(request, pk):
    analysis = _load_analysis(request, pk)
    fit_id = (request.data.get('fit_id') or '').strip()
    if not fit_id:
        return Response({'detail': 'fit_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        set_container_best_fit(analysis, fit_id, request.user)
    except FitContributionError as exc:
        return Response({'detail': str(exc)}, status=exc.status_code)
    return Response({'fits': _fits_list(analysis, request.user)})


@api_view(['GET'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def analysis_fit_parameters_api(request, pk):
    analysis = _load_analysis(request, pk)
    fit_id = request.query_params.get('fit_id') or None
    try:
        rows = fit_parameters_for_api(analysis, fit_id)
    except Exception as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'fit_id': fit_id or 'best', 'parameters': rows})


def _contribute_for_parent(request, *, category, star=None, spectrum=None, lightcurve=None):
    from observations.models import LightCurve, Spectrum
    from stars.models import Star

    upload = request.FILES.get('datafile') or request.FILES.get('file')
    if not upload:
        return Response({'detail': 'Missing fit file (datafile).'}, status=status.HTTP_400_BAD_REQUEST)

    if spectrum is not None:
        spectrum = get_object_or_404(Spectrum.objects.select_related('project', 'star'), pk=spectrum)
        project = spectrum.project
        star = spectrum.star
    elif lightcurve is not None:
        lightcurve = get_object_or_404(LightCurve.objects.select_related('project', 'star'), pk=lightcurve)
        project = lightcurve.project
        star = lightcurve.star
    elif star is not None:
        star = get_object_or_404(Star.objects.select_related('project'), pk=star)
        project = star.project
    else:
        return Response({'detail': 'Parent object required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        check_project_access(request.user, project, require_add=True)
    except PermissionDenied:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    suffix = os.path.splitext(upload.name)[1] or '.h5'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        from analysis.services.fit_contribution import FitContributionError, contribute_to_parent
        container, fit_id = contribute_to_parent(
            project=project,
            category=category,
            user=request.user,
            upload_path=tmp_path,
            star=star,
            spectrum=spectrum if spectrum is not None else None,
            lightcurve=lightcurve if lightcurve is not None else None,
            label=(request.POST.get('label') or '').strip(),
            method=(request.POST.get('method') or '').strip(),
            external_id=(request.POST.get('external_id') or '').strip(),
            set_as_best=request.POST.get('set_as_best', '').lower() in ('1', 'true', 'yes'),
        )
    except FitContributionError as exc:
        return Response({'detail': str(exc)}, status=exc.status_code)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return Response({
        'container_pk': container.pk,
        'fit_id': fit_id,
        'fits': _fits_list(container, request.user),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def contribute_spectral_fit_api(request, spectrum_pk):
    from analysis.categories import AnalysisCategory
    return _contribute_for_parent(request, category=AnalysisCategory.SPECTRAL_FIT, spectrum=spectrum_pk)


@api_view(['POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def contribute_lc_fit_api(request, lightcurve_pk):
    from analysis.categories import AnalysisCategory
    return _contribute_for_parent(request, category=AnalysisCategory.LIGHTCURVE_FIT, lightcurve=lightcurve_pk)


@api_view(['POST'])
@authentication_classes(UPLOAD_AUTH)
@permission_classes([IsAuthenticated])
def contribute_star_fit_api(request, star_pk):
    from analysis.categories import AnalysisCategory
    category = (request.POST.get('category') or request.data.get('category') or '').strip()
    if category not in (AnalysisCategory.RV_CURVE, AnalysisCategory.SED_FIT):
        return Response({'detail': 'category must be rv_curve or sed_fit.'}, status=status.HTTP_400_BAD_REQUEST)
    return _contribute_for_parent(request, category=category, star=star_pk)
