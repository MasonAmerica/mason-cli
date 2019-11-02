import os
import zipfile

from masonlib.internal.artifacts import IArtifact


class Media(IArtifact):

    def __init__(self, name, type, version, binary):
        self.name = str(name)
        self.type = type
        self.version = str(version)
        self.binary = binary
        self.details = None

    @staticmethod
    def parse(config, name, type, version, binary):
        if not os.path.isfile(binary):
            config.logger.error('No file provided')
            return None

        media = Media(name, type, version, binary)

        # Bail on non valid apk
        if not media.is_valid():
            config.logger.error('Not a valid {}, '
                                'see type requirements in the documentation'.format(type))
            return None

        config.logger.info('----------- MEDIA -----------')
        config.logger.info('File Name: {}'.format(media.binary))
        config.logger.info('File size: {}'.format(os.path.getsize(binary)))
        config.logger.info('Name: {}'.format(media.name))
        config.logger.info('Version: {}'.format(media.version))
        config.logger.info('Type: {}'.format(media.type))

        if media.details:
            config.logger.debug('Details: ')
            lines = list(line for line in (l.strip() for l in media.details) if line)
            for line in lines:
                config.logger.debug(line)
        config.logger.info('-----------------------------')

        return media

    def is_valid(self):
        if self.type == 'bootanimation':
            return self._validate_bootanimation()
        else:
            return False

    def get_content_type(self):
        if self.get_sub_type() == 'bootanimation':
            return 'application/zip'
        else:
            return None

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
        with zipfile.ZipFile(self.binary) as zip_file:
            ret = zip_file.testzip()
            desc = zip_file.read('desc.txt')
            with zip_file.open('desc.txt') as filename:
                self.details = filename.readlines()
            if not desc:
                return False
        return ret is None
