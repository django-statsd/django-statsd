from django.core import cache
from django.core.cache.backends.base import BaseCache

from django_statsd import statsd

class StatsdTracker(BaseCache):

    def __init__(self, cache):
        self.cache = cache

    def _key(self):
        return 'cache'

    def add(self, *args, **kw):
        with statsd.timer('%s.add' % self._key()):
            return self.cache.add(*args, **kw)

    def get(self, *args, **kw):
        with statsd.timer('%s.get' % self._key()):
            return self.cache.get(*args, **kw)

    def set(self, *args, **kw):
        with statsd.timer('%s.set' % self._key()):
            return self.cache.set(*args, **kw)

    def delete(self, *args, **kw):
        with statsd.timer('%s.delete' % self._key()):
            return super(StatsdTracker, self).delete(*args, **kw)

    def get_many(self, *args, **kw):
        with statsd.timer('%s.get_many' % self._key()):
            return super(StatsdTracker, self).get_many(*args, **kw)


def patch():
    cache.cache = StatsdTracker(cache.cache)
