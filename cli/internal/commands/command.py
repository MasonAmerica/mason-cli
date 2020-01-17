import abc
from abc import abstractmethod

import six


@six.add_metaclass(abc.ABCMeta)
class Command:
    @abstractmethod
    def run(self):
        pass
