from masonlib.imason import IMason

from masonlib.internal.mason import Mason

class Platform(object):

    def __init__(self, config):
        self.config = config

    def get(self, interface):
        """
        Get a specific interface from the Mason Platform
        :param interface: (ex, IMason)
        :return: instance of the given interface
        """
        if type(interface) is IMason.__class__:
            return Mason(self.config)
        else:
            raise NotImplementedError("Interface " + str(interface) + " is unknown")