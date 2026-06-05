import logging

from celery import shared_task

from observations.auxil import read_lightcurve, read_spectrum

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def process_specfile_task(self, specfile_pk, create_new_star=False, user_info=None):
    logger.info('Processing specfile pk=%s task_id=%s', specfile_pk, self.request.id)
    return read_spectrum.process_specfile(
        specfile_pk,
        create_new_star=create_new_star,
        user_info=user_info or {},
    )


@shared_task(bind=True)
def process_spectrum_task(self, spectrum_pk):
    logger.info('Processing spectrum pk=%s task_id=%s', spectrum_pk, self.request.id)
    return read_spectrum.derive_spectrum_info(spectrum_pk)


@shared_task(bind=True)
def process_raw_specfile_task(self, rawspecfile_pk):
    logger.info('Processing raw specfile pk=%s task_id=%s', rawspecfile_pk, self.request.id)
    return read_spectrum.process_raw_spec(rawspecfile_pk)


@shared_task(bind=True)
def process_lightcurve_task(self, lightcurve_pk):
    logger.info('Processing lightcurve pk=%s task_id=%s', lightcurve_pk, self.request.id)
    return read_lightcurve.process_lightcurve(lightcurve_pk)


@shared_task(bind=True)
def build_bulk_spectra_zip_task(self, project_pk, requested_stars, user_pk):
    import shutil

    from django.contrib.auth import get_user_model

    from observations.services.bulk_download import (
        bulk_download_artifact_path,
        build_zip_archive,
        collect_download_files,
        resolve_spectra_queryset,
    )
    from stars.models import Project

    logger.info('Bulk ZIP project=%s task_id=%s', project_pk, self.request.id)
    user = get_user_model().objects.get(pk=user_pk)
    project = Project.objects.get(pk=project_pk)
    spectra = resolve_spectra_queryset(project, requested_stars, user)
    files_to_return, preferred_filenames = collect_download_files(spectra)
    if not files_to_return:
        return {'error': 'No files matched the selection.'}

    zip_path, temp_directory = build_zip_archive(files_to_return, preferred_filenames)
    dest = bulk_download_artifact_path(self.request.id)
    try:
        shutil.copy2(zip_path, dest)
    finally:
        shutil.rmtree(temp_directory, ignore_errors=True)
    return {'task_id': self.request.id, 'file': dest, 'status': 'ready'}


@shared_task(bind=True)
def process_bulk_upload_task(self, project_pk, specfile_pks, user_pk):
    from django.contrib.auth import get_user_model

    logger.info(
        'Bulk upload processing project=%s specfiles=%s task_id=%s',
        project_pk,
        len(specfile_pks),
        self.request.id,
    )
    user_info = {}
    messages = []
    errors = 0
    for specfile_pk in specfile_pks:
        try:
            success, message = read_spectrum.process_specfile(
                specfile_pk,
                create_new_star=True,
                user_info=user_info,
            )
            messages.append(message)
            if not success:
                errors += 1
        except Exception as exc:
            messages.append(str(exc))
            errors += 1

    return {
        'task_id': self.request.id,
        'messages': messages,
        'errors': errors,
        'processed': len(specfile_pks),
        'user_pk': user_pk,
        'project_pk': project_pk,
    }


@shared_task
def cleanup_bulk_download_artifacts_task():
    from observations.services.bulk_download import cleanup_expired_bulk_downloads

    removed = cleanup_expired_bulk_downloads()
    logger.info('Removed %s expired bulk download ZIP(s)', removed)
    return {'removed': removed}
