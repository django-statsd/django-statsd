from django.db.backends import util
from django_statsd import statsd

class StatsdTracker(util.CursorDebugWrapper):

    def _key(self):
        return '%s.%s' % (self.db.client.executable_name, self.db.alias)

    def execute(self, *args, **kw):
        with statsd.timer('%s.execute' % self._key()):
            return super(StatsdTracker, self).execute(*args, **kw)

    def executemany(self, *args, **kw):
        with statsd.timer('%s.executemany' % self._key()):
            return super(StatsdTracker, self).executemany(*args, **kw)

# TODO: make this work when DEBUG = False
# TODO: play nicer with debug toolbar
def patch():
    util.CursorDebugWrapper = StatsdTracker
