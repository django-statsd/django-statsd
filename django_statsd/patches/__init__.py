from django.conf import settings
from django.utils.importlib import import_module

# Workaround for tests.
try:
    minimal = {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'mydatabase'
            }
        },
        'ROOT_URLCONF': '',
        'STATSD_CLIENT': 'django_statsd.clients.null',
        'STATSD_PREFIX': None,
        'METLOG': None
    }

    if not settings.configured:
        settings.configure(**minimal)

    patches = getattr(settings, 'STATSD_PATCHES', [])
except ImportError:
    patches = []

for patch in patches:
    import_module(patch).patch()
