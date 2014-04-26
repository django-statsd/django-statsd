import django
from django.db.backends import util
from django_statsd.clients import statsd
from django_statsd.patches.utils import wrap


def key(db, attr):
    return 'db.%s.%s.%s' % (db.client.executable_name, db.alias, attr)

def __getattr__(self, attr):
    """
    The CursorWrapper is a pretty small wrapper around the cursor.
    If you are NOT in debug mode, this is the wrapper that's used.
    Sadly if it's in debug mode, we get a different wrapper.
    """
    if django.VERSION < (1, 6) and self.db.is_managed():
        # In Django 1.6 you can't put a connection in managed mode
        self.db.set_dirty()
    if attr in self.__dict__:
        return self.__dict__[attr]
    else:
        if attr in ['execute', 'executemany']:
            return wrap(getattr(self.cursor, attr), key(self.db, attr))
        return getattr(self.cursor, attr)


def wrap_class(base, super_class=None):
    """Returns a sub-class of the argument 'base'
    The sub class has its execute and executemany methods will record query timings.

    If the execute and executemany methods you're overriding makes super()
    calls, the argument super_class can be provided to not break things.
    """

    class Wrapper(base):

        def execute(self, *args, **kwargs):
            with statsd.timer(key(self.db, 'execute')):
                return super(super_class, self).execute(*args, **kwargs)

        def executemany(self, *args, **kwargs):
            with statsd.timer(key(self.db, 'executemany')):
                return super(super_class, self).execute(*args, **kwargs)

    super_class = super_class or Wrapper
    return Wrapper

def patch():
    """
    The CursorWrapper is a pretty small wrapper around the cursor.
    If you are NOT in debug mode, this is the wrapper that's used.
    Sadly if it's in debug mode, we get a different wrapper for version earlier than 1.6.
    """

    if django.VERSION > (1, 6):
        util.CursorDebugWrapper = wrap_class(util.CursorDebugWrapper,
                                                    super_class=util.CursorDebugWrapper)
        util.CursorWrapper = wrap_class(util.CursorWrapper)
    else:
        util.CursorDebugWrapper = wrap_class(util.CursorDebugWrapper)
        util.CursorWrapper.__getattr__ = __getattr__
