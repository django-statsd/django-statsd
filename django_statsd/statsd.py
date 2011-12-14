from django.utils.importlib import import_module
from django.conf import settings

_statsd = None

def get_client():
    client = getattr(settings, 'STATSD_CLIENT', 'statsd.client')
    host = getattr(settings, 'STATSD_HOST', 'localhost')
    port = getattr(settings, 'STATSD_PORT', 8125)
    prefix = getattr(settings, 'STATSD_PREFIX', None)
    return import_module(client).StatsClient(host, port, prefix)

statsd = get_client()

