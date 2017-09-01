import time

from django.core.management.base import BaseCommand

from django_statsd.clients import statsd


class Command(BaseCommand):
    help = """
    Send a ping to statsd, this is suitable for using as a line in graphite
    charts, for example:
    http://codeascraft.etsy.com/2010/12/08/track-every-release/

    `key`: key.to.ping.with
    """

    def add_arguments(self, parser):
        parser.add_argument('--key', action='store', type=str,
                            dest='key', help='Key to ping')

    def handle(self, *args, **kw):
        statsd.timing(kw.get('key'), time.time())
