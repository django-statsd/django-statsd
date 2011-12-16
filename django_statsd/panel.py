from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, ungettext

from debug_toolbar.panels import DebugPanel
from django_statsd.statsd import statsd


class StatsdPanel(DebugPanel):

    name = 'Statsd'
    has_content = True

    def __init__(self, *args, **kw):
        super(StatsdPanel, self).__init__(*args, **kw)
        self.statsd = statsd
        try:
            self.statsd.reset()
        except AttributeError:
            raise ValueError('To use the toolbar, your STATSD_CLIENT must'
                             'be set to django_statsd.clients.toolbar')

    def nav_title(self):
        return _('Statsd')

    def nav_subtitle(self):
        length = len(self.statsd.cache)
        return ungettext('%s record', '%s records', length) % length

    def title(self):
        return _('Statsd')

    def url(self):
        return ''

    def content(self):
        context = self.context.copy()
        config = getattr(settings, 'TOOLBAR_STATSD', {})
        if 'roots' in config:
            for key in ['timers', 'counts']:
                context[key] = config['roots'][key]
        context['graphite'] = config.get('graphite')
        context['statsd'] = self.statsd.cache
        return render_to_string('toolbar_statsd/statsd.html', context)


