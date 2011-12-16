from django.conf import settings
from django.utils.importlib import import_module


patches = settings.STATSD_PATCHES
for patch in patches:
    print '*', patch
    import_module(patch).patch()

