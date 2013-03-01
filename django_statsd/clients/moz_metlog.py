from django_statsd.clients.null import StatsClient
from django.conf import settings


class StatsClient(StatsClient):
    """A client that pushes messages to metlog """

    def __init__(self, host='localhost', port=8125, prefix=None):
        super(StatsClient, self).__init__(host, port, prefix)
        if prefix is None:
            raise AttributeError(
                "Metlog needs settings.STATSD_PREFIX to be defined")

        self._prefix = prefix
        if getattr(settings, 'METLOG', None) is None:
            raise AttributeError(
                "Metlog needs to be configured as settings.METLOG")

        self.metlog = settings.METLOG

    def timing(self, stat, delta, rate=1):
        """Send new timing information. `delta` is in milliseconds."""
        stat = '%s.%s' % (self._prefix, stat)
        self.metlog.timer_send(stat, delta, rate=rate)

    def incr(self, stat, count=1, rate=1):
        """Increment a stat by `count`."""
        stat = '%s.%s' % (self._prefix, stat)
        self.metlog.incr(stat, count, rate=rate)

    def decr(self, stat, count=1, rate=1):
        """Decrement a stat by `count`."""
        stat = '%s.%s' % (self._prefix, stat)
        self.metlog.incr(stat, -count, rate=rate)
