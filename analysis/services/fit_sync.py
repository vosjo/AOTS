"""Sync AnalysisFit rows from HDF5 FITS groups."""

from __future__ import annotations

from django.contrib.auth import get_user_model

from analysis.auxil.multi_fit_hdf5 import list_fits
from analysis.models.analysis_fit import AnalysisFit


def sync_fits_from_hdf5(analysis) -> list[AnalysisFit]:
    """Create/update AnalysisFit rows to match on-disk HDF5 fits."""
    try:
        data = analysis.get_data()
    except Exception:
        return []

    fit_meta = list_fits(data, category=analysis.category)
    seen_ids: set[str] = set()
    User = get_user_model()
    result: list[AnalysisFit] = []

    for meta in fit_meta:
        fit_id = meta['id']
        seen_ids.add(fit_id)
        uploaded_by = None
        uid = meta.get('uploaded_by_user_id')
        if uid:
            uploaded_by = User.objects.filter(pk=uid).first()
        obj, _created = AnalysisFit.objects.update_or_create(
            analysis=analysis,
            fit_id=fit_id,
            defaults={
                'uploaded_by': uploaded_by,
                'label': meta.get('label') or fit_id,
                'method': meta.get('method') or '',
                'is_best_fit': bool(meta.get('is_best_fit')),
                'external_id': meta.get('external_id') or '',
            },
        )
        result.append(obj)

    AnalysisFit.objects.filter(analysis=analysis).exclude(fit_id__in=seen_ids).delete()
    return result
