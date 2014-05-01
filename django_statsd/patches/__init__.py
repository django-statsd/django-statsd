from django.conf import settings
from django.utils.importlib import import_module

patches = getattr(settings, 'STATSD_PATCHES', [])

for patch in patches:
    import_module(patch).patch()
