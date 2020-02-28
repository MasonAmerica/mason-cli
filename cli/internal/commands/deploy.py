import abc

import click
import six

from cli.config import Config
from cli.internal.commands.command import Command
from cli.internal.utils.ui import section
from cli.internal.utils.validation import validate_credentials


@six.add_metaclass(abc.ABCMeta)
class DeployCommand(Command):
    def __init__(self, config: Config, type: str, name: str, version: str, groups: list):
        self.config = config
        self.type = type
        self.name = name
        self.version = version
        self.groups = groups

        validate_credentials(config)

    def deploy_artifact(self):
        self._log_details(self.groups)
        if not self.config.skip_verify:
            click.confirm('Continue deployment?', default=True, abort=True)

        for group in self.groups:
            self.config.api.deploy_artifact(
                self.type, self.name, self.version, group, self.config.push, self.config.no_https)

        self.config.logger.info("{} '{}' deployed.".format(self.type.capitalize(), self.name))

    def _log_details(self, groups: list):
        if len(groups) == 1:
            group_info = 'Group: {}'.format(groups[0])
        else:
            group_info = 'Groups: '
            for num, group in enumerate(groups):
                group_info += group
                if num + 1 < len(groups):
                    group_info += ', '

        with section(self.config, 'Deployment'):
            self.config.logger.info('Name: {}'.format(self.name))
            self.config.logger.info('Type: {}'.format(self.type))
            self.config.logger.info('Version: {}'.format(self.version))
            self.config.logger.info(group_info)
            self.config.logger.info('Push: {}'.format(self.config.push))

            if self.config.no_https:
                self.config.logger.info('')
                self.config.logger.info('***WARNING***')
                self.config.logger.info('--no-https enabled: this deployment will be delivered to '
                                        'devices over HTTP.')
                self.config.logger.info('***WARNING***')

        self.config.logger.info('')


class DeployConfigCommand(DeployCommand):
    def __init__(self, config: Config, name: str, version: str, groups: list):
        super(DeployConfigCommand, self).__init__(config, 'config', name, version, groups)

    @Command.helper('deploy config')
    def run(self):
        self._maybe_inject_version()
        self.deploy_artifact()

    def _maybe_inject_version(self):
        if self.version != 'latest':
            return

        latest_config = self.config.api.get_latest_artifact(self.name, 'config')
        if latest_config:
            self.version = latest_config.get('version')
        else:
            self.config.logger.error("Config '{}' not found, register it first.".format(self.name))
            raise click.Abort()


class DeployApkCommand(DeployCommand):
    def __init__(self, config: Config, name: str, version: str, groups: list):
        super(DeployApkCommand, self).__init__(config, 'apk', name, version, groups)

    @Command.helper('deploy apk')
    def run(self):
        self._maybe_inject_version()
        self.deploy_artifact()

    def _maybe_inject_version(self):
        if self.version != 'latest':
            return

        latest_apk = self.config.api.get_latest_artifact(self.name, 'apk')
        if latest_apk:
            self.version = latest_apk.get('version')
        else:
            self.config.logger.error("Apk '{}' not found, register it first.".format(self.name))
            raise click.Abort()


class DeployOtaCommand(DeployCommand):
    def __init__(self, config: Config, name: str, version: str, groups: list):
        super(DeployOtaCommand, self).__init__(config, 'ota', name, version, groups)

    @Command.helper('deploy ota')
    def run(self):
        self.deploy_artifact()
