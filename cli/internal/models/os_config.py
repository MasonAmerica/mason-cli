import os

import click
import yaml

from cli.internal.models.artifacts import IArtifact
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.logging import LazyLog
from cli.internal.utils.ui import section
from cli.internal.utils.validation import validate_artifact_version


class OSConfig(IArtifact):
    def __init__(self, config, binary, ecosystem):
        self.config = config
        self.binary = binary
        self.ecosystem = ecosystem
        self.os = {}
        self.name = None
        self.version = None

        if type(ecosystem) is dict:
            self.user_binary = self.ecosystem.get('from') or self.binary
            self.os = self.ecosystem.get('os') or {}
            self.name = str(self.os.get('name'))
            self.version = str(self.os.get('version'))

    @staticmethod
    def parse(config, config_yaml):
        with open(config_yaml) as file:
            try:
                ecosystem = yaml.safe_load(file)
            except yaml.YAMLError as err:
                config.logger.error('Invalid configuration file: {}'.format(err))
                raise click.Abort()

        os_config = OSConfig(config, config_yaml, ecosystem)
        os_config.validate()
        return os_config

    def validate(self):
        if not self.ecosystem or not self.os or not self.name or not self.version:
            self.config.logger.error(
                'Not a valid os configuration. For more information on project configuration, view '
                'the full docs here: https://docs.bymason.com/project-config/.')
            raise click.Abort()

        validate_artifact_version(self.config, self.version, self.get_type())

    def log_details(self):
        with section(self.config, self.get_pretty_type()):
            self.config.logger.info('File path: {}'.format(self.user_binary))
            self.config.logger.info('Name: {}'.format(self.name))
            self.config.logger.info('Version: {}'.format(self.version))

            self.config.logger.debug(LazyLog(
                lambda: 'File size: {}'.format(os.path.getsize(self.binary))))
            self.config.logger.debug(LazyLog(
                lambda: 'File SHA256: {}'.format(hash_file(self.binary, 'sha256'))))
            self.config.logger.debug(LazyLog(
                lambda: 'File SHA1: {}'.format(hash_file(self.binary, 'sha1'))))
            self.config.logger.debug(LazyLog(
                lambda: 'File MD5: {}'.format(hash_file(self.binary, 'md5'))))

            self.config.logger.debug('Parsed config:')
            self.config.logger.debug(yaml.safe_dump(self.ecosystem))

    def get_content_type(self):
        return 'text/x-yaml'

    def get_type(self):
        return 'config'

    def get_pretty_type(self):
        return 'OS Config'

    def get_sub_type(self):
        return

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        return

    def get_details(self):
        return self.ecosystem

    def __eq__(self, other):
        return self.binary == other.binary and self.ecosystem == other.ecosystem
