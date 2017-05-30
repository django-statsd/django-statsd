
def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        ROOT_URLCONF='django_statsd.urls',
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'django_statsd',
            'tests',
        ),
        STATSD_CLIENT='django_statsd.clients.null',
        STATSD_PREFIX=None,
        METLOG=None,
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass
