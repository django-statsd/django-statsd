from statsd.client import StatsClient
from django.contrib.humanize.templatetags.humanize import intcomma


class StatsClient(StatsClient):
    """A client that pushes things into a local cache."""

    def __init__(self, *args, **kw):
        super(StatsClient, self).__init__(*args, **kw)
        self.reset()

    def reset(self):
        self.cache = []

    def _send(self, stat, value, rate):
        num, scale = value.split('|')
        value = '%s%s' % (intcomma(int(num)), scale)
        self.cache.append([stat, value, rate])
