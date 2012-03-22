from django.db.backends import util

try:
    has_toolbar = True
    from debug_toolbar.toolbar import loader
except ImportError:
    has_toolbar = False

from django_statsd.patches.utils import wrap


def key(db, attr):
    return 'db.%s.%s.%s' % (db.client.executable_name, db.alias, attr)


def __getattr__(self, attr):
    """
    The CursorWrapper is a pretty small wrapper around the cursor.
    If you are NOT in debug mode, this is the wrapper that's used.
    Sadly if it's in debug mode, we get a different wrapper.
    """
    if self.db.is_managed():
        self.db.set_dirty()
    if attr in self.__dict__:
        return self.__dict__[attr]
    else:
        if attr in ['execute', 'executemany']:
            return wrap(getattr(self.cursor, attr), key(self.db, attr))
        return getattr(self.cursor, attr)


def wrap_class(base):
    class Wrapper(base):
        def execute(self, *args, **kw):
            return wrap(super(Wrapper, self).execute,
                        key(self.db, 'execute'))(*args, **kw)

        def executemany(self, *args, **kw):
            return wrap(super(Wrapper, self).executemany,
                        key(self.db, 'executemany'))(*args, **kw)

    return Wrapper

if has_toolbar:
    # This is where the fun begins. django-debug-toolbar monkey patches
    # util.CursorDebugWrapper so you can't monkey patch that if you want to
    # see the SQL queries that it spits out.
    old = loader.DebugToolbar.load_panels

# Even better, it only does this in the middleware, which is after the patch
# so we monkey patch the loading of the patches. So once the toolbar has done
# it's stuff we write out patch on top of it.
def callback(self, *args, **kw):
    res = old(self, *args, **kw)
    from debug_toolbar.panels import sql
    # This will rewrap so this will work when DEBUG = True and the SQL Panel
    # is used in the toolbar.
    util.CursorDebugWrapper = wrap_class(sql.DatabaseStatTracker)
    return res


def patch():
    if has_toolbar:
        loader.DebugToolbar.load_panels = callback
    # So that it will work when DEBUG = True.
    util.CursorDebugWrapper = wrap_class(util.CursorDebugWrapper)
    # So that it will work when DEBUG = False.
    util.CursorWrapper.__getattr__ = __getattr__
