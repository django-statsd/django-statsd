import logging

from django_statsd.clients.null import StatsClient

log = logging.getLogger('statsd')


class StatsClient(StatsClient):
    """A client that sends messages to the logging framework."""

    def timing(self, stat, delta, rate=1):
        """Send new timing information. `delta` is in milliseconds."""
        log.info('Timing: %s, %s, %s' % (stat, delta, rate))

    def incr(self, stat, count=1, rate=1):
        """Increment a stat by `count`."""
        log.info('Increment: %s, %s, %s' % (stat, count, rate))

    def decr(self, stat, count=1, rate=1):
        """Decrement a stat by `count`."""
        log.info('Decrement: %s, %s, %s' % (stat, count, rate))

    def gauge(self, stat, value, rate=1, delta=False):
        """Set a gauge value."""
        log.info('Gauge: %s, %s%s, %s' % (
            stat, '' if not delta else 'diff ', value, rate))
