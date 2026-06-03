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
