import abc

import click
import six

from cli.internal.commands.command import Command
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials


@six.add_metaclass(abc.ABCMeta)
class DeployCommand(Command):
    def __init__(self, config, type, name, version, groups):
        self.config = config
        self.type = type
        self.name = name
        self.version = version
        self.groups = groups

    def deploy_artifact(self):
        validate_credentials(self.config)

        for group in self.groups:
            self._deploy_to_group(group)

    def _deploy_to_group(self, group):
        self._log_details(group)
        if not self.config.skip_verify:
            click.confirm('Continue deploy?', default=True, abort=True)

        try:
            self.config.api.deploy_artifact(
                self.type, self.name, self.version, group, self.config.push, self.config.no_https)
            self.config.logger.info('Artifact deployed.')
        except ApiError as e:
            e.exit(self.config)
            return

    def _log_details(self, group):
        self.config.logger.info('---------- DEPLOY -----------')

        self.config.logger.info('Name: {}'.format(self.name))
        self.config.logger.info('Type: {}'.format(self.type))
        self.config.logger.info('Version: {}'.format(self.version))
        self.config.logger.info('Group: {}'.format(group))
        self.config.logger.info('Push: {}'.format(self.config.push))

        if self.config.no_https:
            self.config.logger.info('')
            self.config.logger.info('***WARNING***')
            self.config.logger.info('--no-https enabled: this deployment will be delivered to '
                                    'devices over HTTP.')
            self.config.logger.info('***WARNING***')

        self.config.logger.info('-----------------------------')


class DeployConfigCommand(DeployCommand):
    def __init__(self, config, name, version, groups):
        super(DeployConfigCommand, self).__init__(config, 'config', name, version, groups)

    def run(self):
        self.deploy_artifact()


class DeployApkCommand(DeployCommand):
    def __init__(self, config, name, version, groups):
        super(DeployApkCommand, self).__init__(config, 'apk', name, version, groups)

    def run(self):
        self.deploy_artifact()


class DeployOtaCommand(DeployCommand):
    def __init__(self, config, name, version, groups):
        super(DeployOtaCommand, self).__init__(config, 'ota', name, version, groups)

    def run(self):
        if self.name != 'mason-os':
            self.config.logger.warning("Unknown name '{0}' for 'ota' deployments. "
                                       "Forcing it to 'mason-os'".format(self.name))
            self.name = 'mason-os'

        self.deploy_artifact()
