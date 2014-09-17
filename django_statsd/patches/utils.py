from django_statsd.clients import statsd
from functools import partial, wraps


def patch_method(target, name, external_decorator=None):

    def decorator(patch_function):
        original_function = getattr(target, name)

        @wraps(patch_function)
        def wrapper(*args, **kw):
            return patch_function(original_function, *args, **kw)

        setattr(target, name, wrapper)
        return wrapper

    return decorator


def wrapped(method, key, *args, **kw):
    with statsd.timer(key):
        return method(*args, **kw)


def wrap(method, key, *args, **kw):
    return partial(wrapped, method, key, *args, **kw)
