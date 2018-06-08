from datadog import DogStatsd


class StatsClient(DogStatsd):

    def __init__(self, *args, **kwargs):
        # datadog uses `namespace` for our `prefix` setting.
        kwargs['namespace'] = kwargs.pop('prefix', None)
        super(StatsClient, self).__init__(*args, **kwargs)

    # Some compatibility to our statsd API
    incr = DogStatsd.increment
    decr = DogStatsd.decrement
    timer = DogStatsd.timed
