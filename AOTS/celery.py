import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')

app = Celery('AOTS')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

_starmap_daily_crontab = getattr(
    settings,
    'STARMAP_DAILY_REGEN_CRONTAB',
    {'hour': 4, 'minute': 0},
)

app.conf.beat_schedule = {
    'cleanup-bulk-download-artifacts': {
        'task': 'observations.tasks.cleanup_bulk_download_artifacts_task',
        'schedule': crontab(hour=3, minute=30),
    },
    'regenerate-all-starmaps': {
        'task': 'stars.tasks.regenerate_all_starmaps_task',
        'schedule': crontab(**_starmap_daily_crontab),
    },
}
