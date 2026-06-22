import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')

app = Celery('AOTS')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-bulk-download-artifacts': {
        'task': 'observations.tasks.cleanup_bulk_download_artifacts_task',
        'schedule': crontab(hour=3, minute=30),
    },
}
