import abc
from abc import abstractmethod

import six


@six.add_metaclass(abc.ABCMeta)
class IArtifact:

    @abstractmethod
    def is_valid(self):
        pass

    @abstractmethod
    def get_content_type(self):
        pass

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def get_sub_type(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_version(self):
        pass

    @abstractmethod
    def get_registry_meta_data(self):
        pass

    @abstractmethod
    def get_details(self):
        pass
