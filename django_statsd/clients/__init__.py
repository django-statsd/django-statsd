import socket

from django.utils.importlib import import_module
from django.conf import settings

_statsd = None


def get_client():
    client = getattr(settings, 'STATSD_CLIENT', 'statsd.client')
    host = getattr(settings, 'STATSD_HOST', 'localhost')
# This is causing problems with statsd
# gaierror ([Errno -9] Address family for hostname not supported)
# TODO: figure out what to do here.
#    host = socket.gethostbyaddr(host)[2][0]
    port = getattr(settings, 'STATSD_PORT', 8125)
    prefix = getattr(settings, 'STATSD_PREFIX', None)
    return import_module(client).StatsClient(host, port, prefix)

if not _statsd:
    _statsd = get_client()

statsd = _statsd
