import logging

from celery import shared_task

from analysis.services.analysis_ingestion import ingest_analysis_file

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def process_analysis_task(self, analysis_pk):
    logger.info('Processing analysis pk=%s task_id=%s', analysis_pk, self.request.id)
    result = ingest_analysis_file(analysis_pk)
    return result.success, result.message
