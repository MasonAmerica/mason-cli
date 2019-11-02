import os

import yaml

from masonlib.internal.artifacts import IArtifact


class OSConfig(IArtifact):
    def __init__(self, config, ecosystem):
        self.config = config
        self.ecosystem = ecosystem
        self.os = {}
        self.name = None
        self.version = None

        if type(ecosystem) is dict:
            self.os = self.ecosystem.get('os', {})
            self.name = str(self.os.get('name', None))
            self.version = str(self.os.get('version', None))

    @staticmethod
    def parse(config, config_yaml):
        with open(config_yaml) as file:
            try:
                ecosystem = yaml.load(file, Loader=yaml.SafeLoader)
            except yaml.YAMLError as err:
                config.logger.error('Invalid configuration file: {}'.format(err))
                return

        os_config = OSConfig(config, ecosystem)

        # Bail on non valid os config
        if not os_config.is_valid():
            config.logger.error('Not a valid os configuration. For more information on project '
                                'configuration, view the full docs here: '
                                'https://docs.bymason.com/project-config/.')
            return None

        config.logger.info('--------- OS Config ---------')
        config.logger.info('File Name: {}'.format(config_yaml))
        config.logger.info('File size: {}'.format(os.path.getsize(config_yaml)))
        config.logger.info('Name: {}'.format(os_config.name))
        config.logger.info('Version: {}'.format(os_config.version))

        config.logger.debug('Parsed config:')
        config.logger.debug(yaml.dump(ecosystem))

        config.logger.info('-----------------------------')
        return os_config

    def is_valid(self):
        if not self.ecosystem or not self.os or not self.name or not self.version:
            return False

        try:
            value = int(self.version)
            if value > 2147483647 or value < 0:
                raise ValueError('The os configuration version cannot be negative or larger '
                                 'than MAX_INT (2147483647)')
        except ValueError as err:
            self.config.logger.error('Error in configuration file: {}'.format(err))
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
