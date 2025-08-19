import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PerfumeValley.settings')

app = Celery('PerfumeValley')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# Load task modules from all registered Django app configs

from celery.schedules import crontab
app.conf.beat_schedule = {
    'update-shiprocket-tracking-every-15-minutes': {
        'task': 'admin_panel.tasks.fetch_tracking_status',
        'schedule': crontab(minute='*/15'),  # every 15 minutes
    },
}