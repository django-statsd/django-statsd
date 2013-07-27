from statsd.client import StatsClient


class StatsClient(StatsClient):
    """A null client that does nothing."""

    def _after(self, data):
        pass
