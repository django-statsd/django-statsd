from django.conf.urls import url

import django_statsd.views

urlpatterns = [
    url('^record$', django_statsd.views.record, name='django_statsd.record'),
]
