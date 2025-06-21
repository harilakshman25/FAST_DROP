from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fast_drop.settings')

app = Celery('fast_drop')

# Load settings from settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks in all apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
