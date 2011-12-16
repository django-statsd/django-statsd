from statsd.client import StatsClient


class StatsClient(StatsClient):
    """A client that pushes things into a local cache."""

    def __init__(self, *args, **kw):
        super(StatsClient, self).__init__(*args, **kw)
        self.reset()

    def reset(self):
        self.cache = []

    def _send(self, stat, value, rate):
        type_ = 'timer'
        if value.split('|')[1] == 'c':
            type_ = 'count'
        self.cache.append([stat, value, rate, type_])
