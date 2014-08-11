from collections import defaultdict
from time import time

from django_statsd.clients.null import StatsClient


class StatsClient(StatsClient):
    """A client that pushes things into a local cache."""

    def __init__(self, *args, **kw):
        super(StatsClient, self).__init__(*args, **kw)
        self.reset()

    def reset(self):
        self.cache = defaultdict(list)
        self.timings = []

    def timing(self, stat, delta, rate=1):
        """Send new timing information. `delta` is in milliseconds."""
        stat = '%s|timing' % stat
        now = time() * 1000
        self.timings.append([stat, now - delta, delta, now])

    def incr(self, stat, count=1, rate=1):
        """Increment a stat by `count`."""
        stat = '%s|count' % stat
        self.cache[stat].append([count, rate])

    def decr(self, stat, count=1, rate=1):
        """Decrement a stat by `count`."""
        stat = '%s|count' % stat
        self.cache[stat].append([-count, rate])

    def gauge(self, stat, value, rate=1, delta=False):
        """Set a gauge value."""
        stat = '%s|gauge' % stat
        if delta:
            self.cache[stat].append([value, rate])
        else:
            self.cache[stat] = [[value, rate]]

    def set(self, stat, value, rate=1):
        stat = '%s|set' % stat
        self.cache[stat].append([value, rate])
