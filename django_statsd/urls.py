try:
    from django.conf.urls import patterns, url
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    '',
    url('^record$', 'django_statsd.views.record', name='django_statsd.record'),
)
