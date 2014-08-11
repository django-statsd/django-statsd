from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ungettext

from debug_toolbar.panels import Panel
from django_statsd.clients import statsd


def munge(stats):
    # Munge the stats back into something easy for a template.
    results = []
    for stat in sorted(stats.keys()):
        values = stats[stat]
        name, type_ = stat.split('|')
        total = sum([x * y for x, y in values])
        data = {'name': name, 'type': type_,
                'count': len(values),
                'total': total,
                'values': values}
        results.append(data)
    return results


def times(stats):
    results = []
    if not stats:
        return results

    all_start = stats[0][1]
    all_end = max([t[3] for t in stats])
    all_duration = all_end - all_start
    for stat, start, duration, end in stats:
        start_rel = (start - all_start)
        start_ratio = (start_rel / float(all_duration))
        duration_ratio = (duration / float(all_duration))
        try:
            duration_ratio_relative = duration_ratio / (1.0 - start_ratio)
        except ZeroDivisionError:
            duration_ratio_relative = 0
        results.append([stat.split('|')[0],
                        # % start from left.
                        start_ratio * 100.0,
                        # % width
                        duration_ratio_relative * 100.0,
                        duration,
                        ])
    return results


class StatsdPanel(Panel):

    title = _('Statsd')
    has_content = True

    template = 'toolbar_statsd/statsd.html'

    def __init__(self, *args, **kwargs):
        super(StatsdPanel, self).__init__(*args, **kwargs)
        self.statsd = statsd
        try:
            self.statsd.reset()
        except AttributeError:
            raise ValueError('To use the toolbar, your STATSD_CLIENT must'
                             'be set to django_statsd.clients.toolbar')

    @property
    def nav_subtitle(self):
        length = len(self.statsd.cache) + len(self.statsd.timings)
        return ungettext('%s record', '%s records', length) % length

    def process_response(self, request, response):
        config = getattr(settings, 'TOOLBAR_STATSD', {})
        if 'roots' in config:
            for key in ['timers', 'counts']:
                self.record_stats({key: config['roots'][key]})

        self.record_stats({
            'graphite': config.get('graphite'),
            'statsd': munge(self.statsd.cache),
            'timings': times(self.statsd.timings)
        })
