DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase'
    }
}

ROOT_URLCONF = ''
STATSD_CLIENT = 'django_statsd.clients.null'
STATSD_PREFIX = None
METLOG = None

SECRET_KEY = 'secret'
