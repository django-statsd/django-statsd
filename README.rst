Django Statsd
=============

Integration between statsd and django. It allows you to use different clients,
sends timings as middleware and integrates with django debug toolbar.

Credits:

- jbalogh and jsocol for statsd and commonware, which I just ripped parts out
  of and put in here.
- robhudson for django-debug-toolbar

Installation
------------

From pypi::

        pip install django-statsd-mozilla

Because there is already a django-statsd on pypi.

Requirement, pystatsd:

https://github.com/jsocol/pystatsd

First off, pick your client, one of:

- django_statsd.clients.null

  This one does nothing, good for development. No point in wasting those UDP
  packets.

- django_statsd.clients.toolbar

  Use for the django debug toolbar, stores all the statsd pings on the request
  so they can be used in the toolbar.

- django_statsd.clients.normal

  Use this for production, it just passes through to the real actual pystatsd.

Usage
-----

To send timings from your code, use just like pystatsd, but change your imports
to read::

        from django_statsd.clients import statsd

For example::

        from django_statsd.clients import statsd
        statsd.incr('response.200')

Django statsd will choose the client as specified in your config and send the
data to it. You can change you client by specifying it in the config, the
default is::

        STATSD_CLIENT = 'django_statsd.clients.statsd'

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

Note: this must go before the GraphiteMiddleware so that we've got the timing
data in before we show the toolbar panel.

Add in the panel::

        DEBUG_TOOLBAR_PANELS = (
             ...
             'django_statsd.panel.StatsdPanel',
        )

Set the client::

        STATSD_CLIENT = 'django_statsd.clients.toolbar'

Finally if you have production data coming into a graphite server, you can
show data from that server. If you have one, link it up::

Here's the configuration we use on AMO. Because triggers and counts go
to different spots, you can configure them differently::

        TOOLBAR_STATSD = {
                'graphite': 'https://graphite-phx.mozilla.org/render/',
                'roots': {
                        'timers': ['stats.timers.addons-dev', 'stats.timers.addons'],
                        'counts': ['stats.addons-dev', 'stats.addons']
                }
        }

The key is added on to the root. So if you've got a key of `view.GET` this
would look that up on the graphite server with the key::

        stats.addons.view.GET

More
----

- More tests.

- More measuring things.
