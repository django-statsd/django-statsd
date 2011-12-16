Credits:
- jbalogh and jsocol for statsd and commonware.
- robhudson for django-debug-toolbar

Settings:

Adding in the middleware.

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    ) + MIDDLEWARE_CLASSES


Add in the panel, you must remove the SQL panel (hopefully this will get
fixed).

DEBUG_TOOLBAR_PANELS = (
...
#    'debug_toolbar.panels.sql.SQLDebugPanel',
    'django_statsd.panel.StatsdPanel',
)

Pick your client, one of:

- django_statsd.clients.null  (does nothing)
- django_statsd.clients.toolbar  (use for the toolbar)
- django_statsd.clients.statsd  (use for production)

STATSD_CLIENT = 'django_statsd.clients.toolbar'

Pick your patches:

STATSD_PATCHES = [
    'django_statsd.patches.db',
    'django_statsd.patches.cache',
]

Configure where the toolbar shows graphs:

TOOLBAR_STATSD = {
    'graphite': 'https://graphite-phx.mozilla.org/render/',
    'roots': {
        'timers': ['stats.timers.addons-dev', 'stats.timers.addons'],
        'counts': ['stats.addons-dev', 'stats.addons']
    }
}

Phew.
