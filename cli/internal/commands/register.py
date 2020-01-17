import abc

import click
import six

from cli.internal.commands.command import Command
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials


@six.add_metaclass(abc.ABCMeta)
class RegisterCommand(Command):
    def __init__(self, config):
        self.config = config

    def register_artifact(self, binary, artifact):
        validate_credentials(self.config)

        artifact.log_details()
        if not self.config.skip_verify:
            click.confirm('Continue register?', default=True, abort=True)

        self.config.logger.debug('File SHA1: {}'.format(hash_file(binary, 'sha1', True)))
        self.config.logger.debug('File MD5: {}'.format(hash_file(binary, 'md5', True)))

        try:
            self.config.api.upload_artifact(binary, artifact)
            self.config.logger.info('Artifact registered.')
        except ApiError as e:
            e.exit(self.config)
            return


class RegisterConfigCommand(RegisterCommand):
    def __init__(self, config, config_files):
        super(RegisterConfigCommand, self).__init__(config)
        self.config_files = config_files

    def run(self):
        for file in self.config_files:
            self.register_artifact(file, OSConfig.parse(self.config, file))


class RegisterApkCommand(RegisterCommand):
    def __init__(self, config, apk_files):
        super(RegisterApkCommand, self).__init__(config)
        self.apk_files = apk_files

    def run(self):
        for file in self.apk_files:
            self.register_artifact(file, Apk.parse(self.config, file))


class RegisterMediaCommand(RegisterCommand):
    def __init__(self, config, name, type, version, media_file):
        super(RegisterMediaCommand, self).__init__(config)
        self.name = name
        self.type = type
        self.version = version
        self.media_file = media_file

    def run(self):
        self.register_artifact(
            self.media_file,
            Media.parse(self.config, self.name, self.type, self.version, self.media_file))
