import abc
import time
from abc import abstractmethod

import six

from cli.internal.utils.remote import ApiError


@six.add_metaclass(abc.ABCMeta)
class Command:
    @abstractmethod
    def run(self):
        pass

    @staticmethod
    def helper(name: str):
        def decorator(f):
            def wrapper(self, *args, **kwargs):
                start = int(time.time())
                error = None
                try:
                    return f(self, *args, **kwargs)
                except ApiError as e:
                    error = e
                    e.exit(self.config)
                except BaseException as e:
                    error = e
                    raise e
                finally:
                    diff = int(time.time()) - start
                    self.config.analytics.log_event(
                        command=name, duration_seconds=diff, exception=error)

            return wrapper

        return decorator
