import imghdr
import os
import zipfile

import click

from cli.config import Config
from cli.internal.models.artifacts import IArtifact
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.logging import LazyLog
from cli.internal.utils.ui import section


class Media(IArtifact):
    def __init__(self, config: Config, name, type, version, binary):
        self.config = config
        self.name = str(name)
        self.type = type
        self.version = str(version)
        self.binary = binary
        self.details = None

    @staticmethod
    def parse(config, name, type, version, binary):
        if not os.path.isfile(binary):
            config.logger.error('No file provided')
            raise click.Abort()

        media = Media(config, name, type, version, binary)
        media.validate()
        return media

    def validate(self):
        if self.type == 'bootanimation':
            self._validate_bootanimation()
        elif self.type == 'splash':
            self._validate_splash()
        else:
            self.config.logger.error('Unknown media type: {}'.format(self.type))
            raise click.Abort()

    def log_details(self):
        with section(self.config, self.get_pretty_type()):
            self.config.logger.info('File path: {}'.format(self.binary))
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

            if self.details:
                self.config.logger.debug('Details: ')
                lines = list(line.strip() for line in self.details if line)
                for line in lines:
                    self.config.logger.debug(line)

    def get_content_type(self):
        if self.get_sub_type() == 'bootanimation':
            return 'application/zip'
        elif self.get_sub_type() == 'splash':
            return 'image/png'

    def get_type(self):
        return 'media'

    def get_pretty_type(self):
        if self.get_sub_type() == 'bootanimation':
            return 'Boot animation'
        if self.get_sub_type() == 'splash':
            return 'Splash screen'
        else:
            return 'Media'

    def get_sub_type(self):
        return self.type

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        meta_data = {
            'media': {
                'type': self.get_sub_type(),
            },
        }
        return meta_data

    def _validate_bootanimation(self):
        try:
            zip = zipfile.ZipFile(self.binary)
        except zipfile.BadZipFile as e:
            self.config.logger.error('Invalid boot animation: {}'.format(e))
            raise click.Abort()

        with zip as zip_file:
            error = zip_file.testzip()
            if error:
                self.config.logger.error('Invalid boot animation contents: {}'.format(error))
                raise click.Abort()

            try:
                zip_file.read('desc.txt')
            except KeyError:
                self.config.logger.error('Invalid boot animation contents: desc.txt not found')
                raise click.Abort()

            with zip_file.open('desc.txt') as filename:
                self.details = filename.readlines()

    def _validate_splash(self):
        type_ = imghdr.what(self.binary)
        if type_ != 'png':
            self.config.logger.error('Invalid splash screen: only PNGs are supported')
            raise click.Abort()

    def __eq__(self, other):
        return self.binary == other.binary and self.version == other.version
