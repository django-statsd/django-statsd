import json
import logging
import sys

from django.conf import settings
from nose.exc import SkipTest
from nose import tools as nose_tools
try:
    # Python 2.7, Python 3.x
    from unittest import skipUnless
except ImportError:
    # Python 2.6
    from unittest2 import skipUnless

from django import VERSION
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import dictconfig
from django.utils import unittest

import mock
from nose.tools import eq_
from django_statsd.clients import get_client, statsd
from django_statsd.patches import utils
from django_statsd.patches.db import (
    patched_callproc,
    patched_execute,
    patched_executemany,
)
from django_statsd import middleware

cfg = {
    'version': 1,
    'formatters': {},
    'handlers': {
        'test_statsd_handler': {
            'class': 'django_statsd.loggers.errors.StatsdHandler',
        },
    },
    'loggers': {
        'test.logging': {
            'handlers': ['test_statsd_handler'],
        },
    },
}


@mock.patch.object(middleware.statsd, 'incr')
class TestIncr(TestCase):

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

    def test_request_timing_tastypie(self, timing):
        func = lambda x: x
        gmw = middleware.TastyPieRequestTimingMiddleware()
        gmw.process_view(self.req, func, tuple(), {
            'api_name': 'my_api_name',
            'resource_name': 'my_resource_name'
        })
        gmw.process_response(self.req, self.res)
        eq_(timing.call_count, 3)
        names = ['view.my_api_name.my_resource_name.GET',
                 'view.my_api_name.GET',
                 'view.GET']
        for expected, (args, kwargs) in zip(names, timing.call_args_list):
            eq_(expected, args[0])

    def test_request_timing_tastypie_fallback(self, timing):
        func = lambda x: x
        gmw = middleware.TastyPieRequestTimingMiddleware()
        gmw.process_view(self.req, func, tuple(), dict())
        gmw.process_response(self.req, self.res)
        eq_(timing.call_count, 3)
        names = ['view.%s.%s.GET' % (func.__module__, func.__name__),
                 'view.%s.GET' % func.__module__,
                 'view.GET']
        for expected, (args, kwargs) in zip(names, timing.call_args_list):
            eq_(expected, args[0])


class TestClient(unittest.TestCase):

    @mock.patch.object(settings, 'STATSD_CLIENT', 'statsd.client')
    def test_normal(self):
        eq_(get_client().__module__, 'statsd.client')

    @mock.patch.object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.null')
    def test_null(self):
        eq_(get_client().__module__, 'django_statsd.clients.null')

    @mock.patch.object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.toolbar')
    def test_toolbar(self):
        eq_(get_client().__module__, 'django_statsd.clients.toolbar')

    @mock.patch.object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.toolbar')
    def test_toolbar_send(self):
        client = get_client()
        eq_(client.cache, {})
        client.incr('testing')
        eq_(client.cache, {'testing|count': [[1, 1]]})


class TestMetlogClient(TestCase):

    def check_metlog(self):
        try:
            from metlog.config import client_from_dict_config
            return client_from_dict_config
        except ImportError:
            raise SkipTest("Metlog is not installed")

    @nose_tools.raises(AttributeError)
    def test_no_metlog(self):
        with self.settings(STATSD_PREFIX='moz_metlog',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            get_client()

    def _create_client(self):
        client_from_dict_config = self.check_metlog()

        # Need to load within the test in case metlog is not installed
        from metlog.config import client_from_dict_config

        METLOG_CONF = {
            'logger': 'django-statsd',
            'sender': {
                'class': 'metlog.senders.DebugCaptureSender',
            },
        }

        return client_from_dict_config(METLOG_CONF)

    def test_get_client(self):
        metlog = self._create_client()
        with self.settings(METLOG=metlog,
                           STATSD_PREFIX='moz_metlog',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            eq_(client.__module__, 'django_statsd.clients.moz_metlog')

    def test_metlog_incr(self):
        metlog = self._create_client()
        with self.settings(METLOG=metlog,
                           STATSD_PREFIX='moz_metlog',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            eq_(len(client.metlog.sender.msgs), 0)
            client.incr('testing')
            eq_(len(client.metlog.sender.msgs), 1)

            msg = json.loads(client.metlog.sender.msgs[0])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '1')
            eq_(msg['fields']['rate'], 1)
            eq_(msg['fields']['name'], 'moz_metlog.testing')
            eq_(msg['type'], 'counter')

    def test_metlog_decr(self):
        metlog = self._create_client()
        with self.settings(METLOG=metlog,
                           STATSD_PREFIX='moz_metlog',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            eq_(len(client.metlog.sender.msgs), 0)
            client.decr('testing')
            eq_(len(client.metlog.sender.msgs), 1)

            msg = json.loads(client.metlog.sender.msgs[0])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '-1')
            eq_(msg['fields']['rate'], 1)
            eq_(msg['fields']['name'], 'moz_metlog.testing')
            eq_(msg['type'], 'counter')

    def test_metlog_timing(self):
        metlog = self._create_client()
        with self.settings(METLOG=metlog,
                           STATSD_PREFIX='moz_metlog',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            eq_(len(client.metlog.sender.msgs), 0)
            client.timing('testing', 512, rate=2)
            eq_(len(client.metlog.sender.msgs), 1)

            msg = json.loads(client.metlog.sender.msgs[0])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '512')
            eq_(msg['fields']['rate'], 2)
            eq_(msg['fields']['name'], 'moz_metlog.testing')
            eq_(msg['type'], 'timer')

    @nose_tools.raises(AttributeError)
    def test_metlog_no_prefixes(self):
        metlog = self._create_client()

        with self.settings(METLOG=metlog,
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            client.incr('foo', 2)

    def test_metlog_prefixes(self):
        metlog = self._create_client()

        with self.settings(METLOG=metlog,
                           STATSD_PREFIX='some_prefix',
                           STATSD_CLIENT='django_statsd.clients.moz_metlog'):
            client = get_client()
            eq_(len(client.metlog.sender.msgs), 0)

            client.timing('testing', 512, rate=2)
            client.incr('foo', 2)
            client.decr('bar', 5)

            eq_(len(client.metlog.sender.msgs), 3)

            msg = json.loads(client.metlog.sender.msgs[0])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '512')
            eq_(msg['fields']['rate'], 2)
            eq_(msg['fields']['name'], 'some_prefix.testing')
            eq_(msg['type'], 'timer')

            msg = json.loads(client.metlog.sender.msgs[1])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '2')
            eq_(msg['fields']['rate'], 1)
            eq_(msg['fields']['name'], 'some_prefix.foo')
            eq_(msg['type'], 'counter')

            msg = json.loads(client.metlog.sender.msgs[2])
            eq_(msg['severity'], 6)
            eq_(msg['payload'], '-5')
            eq_(msg['fields']['rate'], 1)
            eq_(msg['fields']['name'], 'some_prefix.bar')
            eq_(msg['type'], 'counter')


# This is primarily for Zamboni, which loads in the custom middleware
# classes, one of which, breaks posts to our url. Let's stop that.
@mock.patch.object(settings, 'MIDDLEWARE_CLASSES', [])
class TestRecord(TestCase):

    urls = 'django_statsd.urls'

    def setUp(self):
        super(TestRecord, self).setUp()
        self.url = reverse('django_statsd.record')
        settings.STATSD_RECORD_GUARD = None
        self.good = {'client': 'boomerang', 'nt_nav_st': 1,
                     'nt_domcomp': 3}
        self.stick = {'client': 'stick',
                      'window.performance.timing.domComplete': 123,
                      'window.performance.timing.domInteractive': 456,
                      'window.performance.timing.domLoading': 789,
                      'window.performance.timing.navigationStart': 0,
                      'window.performance.navigation.redirectCount': 3,
                      'window.performance.navigation.type': 1}

    def test_no_client(self):
        assert self.client.get(self.url).status_code == 400

    def test_no_valid_client(self):
        assert self.client.get(self.url, {'client': 'no'}).status_code == 400

    def test_boomerang_almost(self):
        assert self.client.get(self.url,
                               {'client': 'boomerang'}).status_code == 400

    def test_boomerang_minimum(self):
        content = self.client.get(self.url,
                                  {'client': 'boomerang',
                                   'nt_nav_st': 1}).content.decode()
        assert(content == 'recorded')

    @mock.patch('django_statsd.views.process_key')
    def test_boomerang_something(self, process_key):
        content = self.client.get(self.url, self.good).content.decode()
        assert content == 'recorded'
        assert process_key.called

    def test_boomerang_post(self):
        assert self.client.post(self.url, self.good).status_code == 405

    def test_good_guard(self):
        settings.STATSD_RECORD_GUARD = lambda r: None
        assert self.client.get(self.url, self.good).status_code == 200

    def test_bad_guard(self):
        settings.STATSD_RECORD_GUARD = lambda r: HttpResponseForbidden()
        assert self.client.get(self.url, self.good).status_code == 403

    def test_stick_get(self):
        assert self.client.get(self.url, self.stick).status_code == 405

    @mock.patch('django_statsd.views.process_key')
    def test_stick(self, process_key):
        assert self.client.post(self.url, self.stick).status_code == 200
        assert process_key.called

    def test_stick_start(self):
        data = self.stick.copy()
        del data['window.performance.timing.navigationStart']
        assert self.client.post(self.url, data).status_code == 400

    @mock.patch('django_statsd.views.process_key')
    def test_stick_missing(self, process_key):
        data = self.stick.copy()
        del data['window.performance.timing.domInteractive']
        assert self.client.post(self.url, data).status_code == 200
        assert process_key.called

    def test_stick_garbage(self):
        data = self.stick.copy()
        data['window.performance.timing.domInteractive'] = '<alert>'
        assert self.client.post(self.url, data).status_code == 400

    def test_stick_some_garbage(self):
        data = self.stick.copy()
        data['window.performance.navigation.redirectCount'] = '<alert>'
        assert self.client.post(self.url, data).status_code == 400

    def test_stick_more_garbage(self):
        data = self.stick.copy()
        data['window.performance.navigation.type'] = '<alert>'
        assert self.client.post(self.url, data).status_code == 400


@mock.patch.object(middleware.statsd, 'incr')
class TestErrorLog(TestCase):

    def setUp(self):
        dictconfig.dictConfig(cfg)
        self.log = logging.getLogger('test.logging')

    def division_error(self):
        try:
            1 / 0
        except:
            return sys.exc_info()

    def test_emit(self, incr):
        self.log.error('blargh!', exc_info=self.division_error())
        assert incr.call_args[0][0] == 'error.zerodivisionerror'

    def test_not_emit(self, incr):
        self.log.error('blargh!')
        assert not incr.called


class TestPatchMethod(TestCase):

    def setUp(self):
        super(TestPatchMethod, self).setUp()

        class DummyClass(object):

            def sumargs(self, a, b, c=3, d=4):
                return a + b + c + d

            def badfn(self, a, b=2):
                raise ValueError

        self.cls = DummyClass

    def test_late_patching(self):
        """
        Objects created before patching should get patched as well.
        """
        def patch_fn(original_fn, self, *args, **kwargs):
            return original_fn(self, *args, **kwargs) + 10

        obj = self.cls()
        self.assertEqual(obj.sumargs(1, 2, 3, 4), 10)
        utils.patch_method(self.cls, 'sumargs')(patch_fn)
        self.assertEqual(obj.sumargs(1, 2, 3, 4), 20)

    def test_doesnt_call_original_implicitly(self):
        """
        Original fn must be called explicitly from patched to be
        executed.
        """
        def patch_fn(original_fn, self, *args, **kwargs):
            return 10

        with self.assertRaises(ValueError):
            obj = self.cls()
            obj.badfn(1, 2)

        utils.patch_method(self.cls, 'badfn')(patch_fn)
        self.assertEqual(obj.badfn(1, 2), 10)

    def test_args_kwargs_are_honored(self):
        """
        Args and kwargs must be honored between calls from the patched to
        the original version.
        """
        def patch_fn(original_fn, self, *args, **kwargs):
            return original_fn(self, *args, **kwargs)

        utils.patch_method(self.cls, 'sumargs')(patch_fn)
        obj = self.cls()
        self.assertEqual(obj.sumargs(1, 2), 10)
        self.assertEqual(obj.sumargs(1, 1, d=1), 6)
        self.assertEqual(obj.sumargs(1, 1, 1, 1), 4)

    def test_patched_fn_can_receive_arbitrary_arguments(self):
        """
        Args and kwargs can be received arbitrarily with no contraints on
        the patched fn, even if the original_fn had a fixed set of
        allowed args and kwargs.
        """
        def patch_fn(original_fn, self, *args, **kwargs):
            return args, kwargs

        utils.patch_method(self.cls, 'badfn')(patch_fn)
        obj = self.cls()
        self.assertEqual(obj.badfn(1, d=2), ((1,), {'d': 2}))
        self.assertEqual(obj.badfn(1, d=2), ((1,), {'d': 2}))
        self.assertEqual(obj.badfn(1, 2, c=1, d=2), ((1, 2), {'c': 1, 'd': 2}))


class TestCursorWrapperPatching(TestCase):
    example_queries = {
        'select': 'select * from something;',
        'insert': 'insert (1, 2) into something;',
        'update': 'update something set a=1;',
    }

    def test_patched_callproc_calls_timer(self):
        for operation, query in self.example_queries.items():
            with mock.patch.object(statsd, 'timer') as timer:
                client = mock.Mock(executable_name='client_executable_name')
                db = mock.Mock(executable_name='name', alias='alias', client=client)
                instance = mock.Mock(db=db)

                patched_callproc(lambda *args, **kwargs: None, instance, query)

                self.assertEqual(timer.call_count, 1)
                self.assertEqual(timer.call_args[0][0], 'db.client_executable_name.alias.callproc.%s' % operation)

    def test_patched_execute_calls_timer(self):
        for operation, query in self.example_queries.items():
            with mock.patch.object(statsd, 'timer') as timer:
                client = mock.Mock(executable_name='client_executable_name')
                db = mock.Mock(executable_name='name', alias='alias', client=client)
                instance = mock.Mock(db=db)

                patched_execute(lambda *args, **kwargs: None, instance, query)

                self.assertEqual(timer.call_count, 1)
                self.assertEqual(timer.call_args[0][0], 'db.client_executable_name.alias.execute.%s' % operation)

    def test_patched_executemany_calls_timer(self):
        for operation, query in self.example_queries.items():
            with mock.patch.object(statsd, 'timer') as timer:
                client = mock.Mock(executable_name='client_executable_name')
                db = mock.Mock(executable_name='name', alias='alias', client=client)
                instance = mock.Mock(db=db)

                patched_executemany(lambda *args, **kwargs: None, instance, query)

                self.assertEqual(timer.call_count, 1)
                self.assertEqual(timer.call_args[0][0], 'db.client_executable_name.alias.executemany.%s' % operation)

    @mock.patch(
        'django_statsd.patches.db.pre_django_1_6_cursorwrapper_getattr')
    @mock.patch('django_statsd.patches.db.patched_executemany')
    @mock.patch('django_statsd.patches.db.patched_execute')
    @mock.patch('django.db.backends.util.CursorDebugWrapper')
    @skipUnless(VERSION < (1, 6, 0), "CursorWrapper Patching for Django<1.6")
    def test_cursorwrapper_patching(self,
                                    CursorDebugWrapper,
                                    execute,
                                    executemany,
                                    _getattr):
        try:
            from django.db.backends import utils as util
        except ImportError:
            from django.db.backends import util
        try:
            # We need to patch CursorWrapper like this because setting
            # __getattr__ on Mock instances raises AttributeError.
            class CursorWrapper(object):
                pass

            _CursorWrapper = util.CursorWrapper
            util.CursorWrapper = CursorWrapper

            from django_statsd.patches.db import patch
            execute.__name__ = 'execute'
            executemany.__name__ = 'executemany'
            _getattr.__name__ = '_getattr'
            execute.return_value = 'execute'
            executemany.return_value = 'executemany'
            _getattr.return_value = 'getattr'
            patch()

            self.assertEqual(CursorDebugWrapper.execute(), 'execute')
            self.assertEqual(CursorDebugWrapper.executemany(), 'executemany')
            self.assertEqual(CursorWrapper.__getattr__(), 'getattr')
        finally:
            util.CursorWrapper = _CursorWrapper

    @mock.patch('django_statsd.patches.db.patched_callproc')
    @mock.patch('django_statsd.patches.db.patched_executemany')
    @mock.patch('django_statsd.patches.db.patched_execute')
    @mock.patch('django.db.backends.util.CursorWrapper')
    @skipUnless(VERSION >= (1, 6, 0), "CursorWrapper Patching for Django>=1.6")
    def test_cursorwrapper_patching16(self,
                                      CursorWrapper,
                                      execute,
                                      executemany,
                                      callproc):
        from django_statsd.patches.db import patch
        execute.__name__ = 'execute'
        executemany.__name__ = 'executemany'
        callproc.__name__ = 'callproc'
        execute.return_value = 'execute'
        executemany.return_value = 'executemany'
        callproc.return_value = 'callproc'
        patch()

        self.assertEqual(CursorWrapper.execute(), 'execute')
        self.assertEqual(CursorWrapper.executemany(), 'executemany')
        self.assertEqual(CursorWrapper.callproc(), 'callproc')
