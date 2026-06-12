import logging

from celery import shared_task

from analysis.auxil import process_analyses

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def process_analysis_task(self, analysis_pk):
    logger.info('Processing analysis pk=%s task_id=%s', analysis_pk, self.request.id)
    return process_analyses.process_analysis_file(analysis_pk)
