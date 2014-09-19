from .celery import register_celery_events
from django.conf import settings

if getattr(settings, 'STATSD_CELERY_SIGNALS', False):
    register_celery_events()
