Integration between statsd and django. It allows you to use different clients,
sends timings as middleware and integrates with django debug toolbar.

Requirement, pystatsd: https://github.com/jsocol/pystatsd

First off, pick your client, one of:

- django_statsd.clients.null  (does nothing, good for development)
- django_statsd.clients.toolbar  (use for the toolbar)
- django_statsd.clients.statsd  (use for production, just passes through to pystatsd)

Usage
-----

To send timings from your code, use just like statsd, but change your imports
to read::

        from django_statsd.clients import statsd

For example::

        from django_statsd.clients import statsd
        statsd.incr('response.200')

To send timings or counts with every request, add in some middleware::

        MIDDLEWARE_CLASSES = (
                'django_statsd.middleware.GraphiteRequestTimingMiddleware',
                'django_statsd.middleware.GraphiteMiddleware',
                ) + MIDDLEWARE_CLASSES

To get timings for your database or your cache, put in some monkeypatches::

        STATSD_PATCHES = [
                'django_statsd.patches.db',
                'django_statsd.patches.cache',
        ]

Toolbar integration
-------------------

This will show you the statsd timings in the toolbar::

        MIDDLEWARE_CLASSES = (
                'debug_toolbar.middleware.DebugToolbarMiddleware',
                ) + MIDDLEWARE_CLASSES

Note: this must go before the GraphiteMiddleware.

Add in the panel::

        DEBUG_TOOLBAR_PANELS = (
             ...
             'django_statsd.panel.StatsdPanel',
        )

Set the client::

        STATSD_CLIENT = 'django_statsd.clients.toolbar'

Finally, to show data from a graphite server, if you have one, link it up::

Configure where the toolbar shows graphs::

        TOOLBAR_STATSD = {
                'graphite': 'https://graphite-phx.mozilla.org/render/',
                'roots': {
                        'timers': ['stats.timers.addons-dev', 'stats.timers.addons'],
                        'counts': ['stats.addons-dev', 'stats.addons']
                }
        }

Credits:

- jbalogh and jsocol for statsd and commonware, which I just ripped out
  and put in here.
- robhudson for django-debug-toolbar
