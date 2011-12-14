Todo: write this



A tool that mashes up django-debug-toolbar, graphite, statsd and pystatsd.

Before you can think about getting this to work you'll need:

- A graphite server running and processing the data from statsd

- Some Django middleware or code that sends the data to statsd

Pystatsd: https://github.com/andymckay/pystatsd

Graphite: http://graphite.wikidot.com/installation

Django debug toolbar: https://github.com/django-debug-toolbar/django-debug-toolbar

An example Django app that logs to statsd on each request can be found in
nuggets: https://github.com/mozilla/nuggets

It works by adding the following to your middleware::

    MIDDLEWARE_CLASSES = (
        'commonware.response.middleware.GraphiteRequestTimingMiddleware',
        'commonware.response.middleware.GraphiteMiddleware',
    )

If you've got that setup, to your settings, add the following::

    DEBUG_TOOLBAR_PANELS = (
        ...
        'toolbar_statsd.panel.StatsdPanel'
    )

    STATSD_CLIENT = 'toolbar_statsd.panel'

    TOOLBAR_STATSD = {
        'graphite': 'http://your.graphite.server',
        'roots': ['root.key.for.dev', 'root.key.for.stage']
    }

    INSTALLED_APPS = (
        ...
        'toolbar_statsd'
    )

Notes: django-debug-toolbar middleware must come *after* graphite middleware.

See: example.png for an example of the fun that can be had.
