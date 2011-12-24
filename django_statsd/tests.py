from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.test.client import Client
from django.test.client import RequestFactory
from django.utils import unittest

import mock
import sys
from nose.tools import eq_

from django_statsd.clients import get_client
from django_statsd import middleware


@mock.patch.object(middleware.statsd, 'incr')
class TestIncr(unittest.TestCase):

    def setUp(self):
        self.req = RequestFactory().get('/')
        self.res = HttpResponse()

    def test_graphite_response(self, incr):
        gmw = middleware.GraphiteMiddleware()
        gmw.process_response(self.req, self.res)
        assert incr.called

    def test_graphite_response_authenticated(self, incr):
        self.req.user = mock.Mock()
        self.req.user.is_authenticated.return_value = True
        gmw = middleware.GraphiteMiddleware()
        gmw.process_response(self.req, self.res)
        eq_(incr.call_count, 2)

    def test_graphite_exception(self, incr):
        gmw = middleware.GraphiteMiddleware()
        gmw.process_exception(self.req, None)
        assert incr.called

    def test_graphite_exception_authenticated(self, incr):
        self.req.user = mock.Mock()
        self.req.user.is_authenticated.return_value = True
        gmw = middleware.GraphiteMiddleware()
        gmw.process_exception(self.req, None)
        eq_(incr.call_count, 2)


@mock.patch.object(middleware.statsd, 'timing')
class TestTiming(unittest.TestCase):

    def setUp(self):
        self.req = RequestFactory().get('/')
        self.res = HttpResponse()

    def test_request_timing(self, timing):
        func = lambda x: x
        gmw = middleware.GraphiteRequestTimingMiddleware()
        gmw.process_view(self.req, func, tuple(), dict())
        gmw.process_response(self.req, self.res)
        eq_(timing.call_count, 3)
        names = ['view.%s.%s.GET' % (func.__module__, func.__name__),
                 'view.%s.GET' % func.__module__,
                 'view.GET']
        for expected, (args, kwargs) in zip(names, timing.call_args_list):
            eq_(expected, args[0])

    def test_request_timing_exception(self, timing):
        func = lambda x: x
        gmw = middleware.GraphiteRequestTimingMiddleware()
        gmw.process_view(self.req, func, tuple(), dict())
        gmw.process_exception(self.req, self.res)
        eq_(timing.call_count, 3)
        names = ['view.%s.%s.GET' % (func.__module__, func.__name__),
                 'view.%s.GET' % func.__module__,
                 'view.GET']
        for expected, (args, kwargs) in zip(names, timing.call_args_list):
            eq_(expected, args[0])


class TestClient(unittest.TestCase):

    @mock.patch_object(settings, 'STATSD_CLIENT', 'statsd.client')
    def test_normal(self):
        eq_(get_client().__module__, 'statsd.client')

    @mock.patch_object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.null')
    def test_null(self):
        eq_(get_client().__module__, 'django_statsd.clients.null')

    @mock.patch_object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.toolbar')
    def test_toolbar(self):
        eq_(get_client().__module__, 'django_statsd.clients.toolbar')

    @mock.patch_object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.toolbar')
    def test_toolbar_send(self):
        client = get_client()
        eq_(client.cache, {})
        client.incr('testing')
        eq_(client.cache, {'testing|count': [[1, 1]]})


class TestRecord(unittest.TestCase):

    def setUp(self):
        settings.STATSD_RECORD_GUARD = None
        self.url = reverse('django_statsd.record')
        self.client = Client()
        self.good =  {'client': 'boomerang', 'nt_nav_st': 1,
                      'nt_domcomp': 3}

    def test_no_client(self):
        self.assertRaises(ValueError, self.client.get, self.url)

    def test_no_valid_client(self):
        self.assertRaises(ValueError, self.client.get, self.url,
                          {'client': 'noo!'})

    def test_boomerang_almost(self):
        self.assertRaises(ValueError, self.client.get, self.url,
                          {'client': 'boomerang'})

    def test_boomerang_minimum(self):
        self.client.get(self.url, {'client': 'boomerang', 'nt_nav_st': 1})

    def test_boomerang_something(self):
        self.client.get(self.url, self.good)
        # TODO: figure out how to test this properly, that something
        # got written which isn't that easy.

    def test_good_guard(self):
        settings.STATSD_RECORD_GUARD = lambda r: None
        self.client.get(self.url, self.good)

    def test_bad_guard(self):
        settings.STATSD_RECORD_GUARD = lambda r: HttpResponseForbidden()
        assert self.client.get(self.url, self.good).status_code == 403

