import os
import yaml

from masonlib.internal.artifacts import IArtifact


class OSConfig(IArtifact):

    def __init__(self, ecosystem):
        self.ecosystem = ecosystem
        if ecosystem:
            self.os = self.ecosystem['os']
            self.name = str(self.os['name'])
            self.version = str(self.os['version'])

    @staticmethod
    def parse(config, config_yaml):
        if not os.path.isfile(config_yaml):
            print('No file provided')
            return None

        ecosystem = OSConfig._load_ecosystem(config_yaml)
        os_config = OSConfig(ecosystem)

        # Bail on non valid os config
        if not os_config.is_valid():
            print("Not a valid os configuration, please see https://docs.bymason.com for further details.")
            return None

        print('--------- OS Config ---------')
        print('File Name: {}'.format(config_yaml))
        print('File size: {}'.format(os.path.getsize(config_yaml)))
        print('Name: {}'.format(os_config.name))
        print('Version: {}'.format(os_config.version))
        if config.verbose:
            for k, v in os_config.ecosystem.items():
                print(k, v)
        print('-----------------------------')
        return os_config

    def is_valid(self):
        if not self.ecosystem or not self.os or not self.name or not self.version:
            return False
        try:
            value = int(self.version)
            if value > 2147483647 or value < 0:
                raise ValueError('The os configuration version cannot be negative or larger than MAX_INT (2147483647)')
        except ValueError as err:
            print('Error in configuration file: {}'.format(err))
            return False
        return True

    def get_content_type(self):
        return 'text/x-yaml'

    def get_type(self):
        return 'config'

    def get_sub_type(self):
        return None

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        return None

    def get_details(self):
        return self.ecosystem

    @staticmethod
    def _load_ecosystem(path):
        if not os.path.isfile(path):
            return None

        with open(path) as data_file:
            try:
                data = yaml.load(data_file, Loader=yaml.SafeLoader)
                return data
            except yaml.YAMLError as err:
                print('Error in configuration file: {}'.format(err))
                return None
