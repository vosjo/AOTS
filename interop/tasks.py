import logging

from celery import shared_task

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def import_astra_task(self, project_pk, file_path, star_names=None):
    import os

    from interop.import_service import import_astra_package
    from stars.models import Project

    logger.info('ASTRA import project=%s task_id=%s', project_pk, self.request.id)
    project = Project.objects.get(pk=project_pk)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as fh:
            raw = fh.read()
        try:
            os.unlink(file_path)
        except OSError:
            pass
    else:
        from django.core.files.storage import default_storage

        with default_storage.open(file_path, 'rb') as fh:
            raw = fh.read()
    batch, result = import_astra_package(project, raw, star_names=star_names or None)
    return {
        'task_id': self.request.id,
        'batch_id': batch.pk,
        'status': batch.status,
        'summary': batch.summary,
        'warnings': result.warnings,
    }


@shared_task(bind=True)
def export_astra_task(self, project_pk, star_ids, options=None):
    import os
    import shutil

    from django.conf import settings

    from dataclasses import fields

    from interop.export_service import ExportOptions, export_astra_package
    from interop.filenames import sanitize_astra_filename
    from stars.models import Project

    logger.info('ASTRA export project=%s task_id=%s', project_pk, self.request.id)
    project = Project.objects.get(pk=project_pk)
    raw_options = dict(options or {})
    download_filename = sanitize_astra_filename(
        raw_options.pop('download_filename', ''),
        default=f'aots_export_{project.slug}.astra',
    )
    export_fields = {f.name for f in fields(ExportOptions)}
    opts = ExportOptions(**{k: v for k, v in raw_options.items() if k in export_fields})
    payload = export_astra_package(project, star_ids, opts)

    directory = os.path.join(settings.MEDIA_ROOT, 'interop_exports')
    os.makedirs(directory, exist_ok=True)
    dest = os.path.join(directory, f'{self.request.id}.astra')
    with open(dest, 'wb') as fh:
        fh.write(payload)
    return {
        'task_id': self.request.id,
        'file': dest,
        'status': 'ready',
        'download_filename': download_filename,
    }
