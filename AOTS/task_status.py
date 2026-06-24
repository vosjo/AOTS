"""
Build JSON payloads for Celery task status (polling and admin monitor).
"""

from celery.result import AsyncResult

TASK_DISPLAY_NAMES = {
    'observations.tasks.build_bulk_download_zip_task': 'Bulk download',
    'observations.tasks.process_bulk_upload_task': 'Bulk upload',
    'stars.tasks.fetch_gaia_bulk_task': 'Gaia DR3 fetch',
    'stars.tasks.fetch_tess_bulk_task': 'TESS fetch',
    'stars.tasks.sync_simbad_identifiers_bulk_task': 'Simbad aliases',
    'observations.tasks.process_specfile_task': 'Process specfile',
    'observations.tasks.process_spectrum_task': 'Process spectrum',
    'observations.tasks.process_raw_specfile_task': 'Process raw specfile',
    'observations.tasks.process_lightcurve_task': 'Process light curve',
    'analysis.tasks.process_analysis_task': 'Process analysis',
}


def task_display_name(task_name):
    if not task_name:
        return 'Background task'
    return TASK_DISPLAY_NAMES.get(task_name, task_name.rsplit('.', 1)[-1].replace('_', ' '))


def build_task_status_payload(task_id, registration=None):
    result = AsyncResult(task_id)
    payload = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
    }

    if registration:
        task_name = registration.get('task_name') or ''
        payload.update({
            'user_id': registration.get('user_id'),
            'project_id': registration.get('project_id'),
            'task_name': task_name,
            'task_display': task_display_name(task_name),
            'label': registration.get('label') or '',
            'created_at': registration.get('created_at'),
        })

    if result.status == 'PROGRESS' and isinstance(result.info, dict):
        payload['meta'] = result.info
        meta = result.info
        current = meta.get('current')
        total = meta.get('total')
        star_name = meta.get('star_name')
        if current is not None and total:
            progress = f'{current}/{total}'
            if star_name:
                progress += f' ({star_name})'
            payload['progress'] = progress

    if result.failed():
        payload['error'] = str(result.result)
    elif result.successful():
        payload['result'] = result.result

    return payload
