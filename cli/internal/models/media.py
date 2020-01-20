import os
import zipfile

import click

from cli.internal.models.artifacts import IArtifact


class Media(IArtifact):

    def __init__(self, config, name, type, version, binary):
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

    def log_details(self):
        self.config.logger.info('----------- MEDIA -----------')
        self.config.logger.info('File Name: {}'.format(self.binary))
        self.config.logger.info('File size: {}'.format(os.path.getsize(self.binary)))
        self.config.logger.info('Name: {}'.format(self.name))
        self.config.logger.info('Version: {}'.format(self.version))
        self.config.logger.info('Type: {}'.format(self.type))

        if self.details:
            self.config.logger.debug('Details: ')
            lines = list(line for line in (l.strip() for l in self.details) if line)
            for line in lines:
                self.config.logger.debug(line)
        self.config.logger.info('-----------------------------')

    def get_content_type(self):
        if self.get_sub_type() == 'bootanimation':
            return 'application/zip'

    def get_type(self):
        return 'media'

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

    def get_details(self):
        return self.details

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

    def __eq__(self, other):
        return self.binary == other.binary
