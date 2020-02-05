import abc
from abc import abstractmethod

import six


@six.add_metaclass(abc.ABCMeta)
class Command:
    @abstractmethod
    def run(self):
        pass

    @staticmethod
    def log(name):
        def decorator(f):
            def wrapper(self, *args, **kwargs):
                error = None
                try:
                    return f(self, *args, **kwargs)
                except BaseException as e:
                    error = e
                    raise e
                finally:
                    self.config.analytics.log_event(command=name, exception=error)

            return wrapper

        return decorator
