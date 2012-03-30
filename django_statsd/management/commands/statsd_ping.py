from optparse import make_option

from django.core.management.base import BaseCommand

from django_statsd.clients import statsd


class Command(BaseCommand):
    help = """
    Send a ping to statsd
    `key`: key.to.ping.with
    """
    option_list = BaseCommand.option_list + (
        make_option('--key', action='store', type='string',
                    dest='key', help='Key to ping'),
    )

    def handle(self, *args, **kw):
        statsd.incr(kw.get('key'))

