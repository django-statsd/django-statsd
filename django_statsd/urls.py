from django.conf.urls import url


urlpatterns = [
    url('^record$', 'django_statsd.views.record', name='django_statsd.record'),
]
