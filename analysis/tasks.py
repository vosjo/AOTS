import logging

from celery import shared_task

from analysis.auxil import process_datasets

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def process_dataset_task(self, dataset_pk):
    logger.info('Processing dataset pk=%s task_id=%s', dataset_pk, self.request.id)
    return process_datasets.process_analysis_file(dataset_pk)
