import inspect
import time
from urllib.parse import urlparse

import click

from cli.config import Config
from cli.internal.commands.command import Command
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials


class BuildCommand(Command):
    def __init__(
        self,
        config: Config,
        project: str,
        version: str,
        block: bool,
        mason_version: str,
        time=time,
        urlparse=urlparse
    ):
        super(BuildCommand, self).__init__(config)

        self.project = project
        self.version = version
        self.block = block
        self.mason_version = mason_version
        self.time = time
        self.urlparse = urlparse

        validate_credentials(config)

    @Command.helper('build')
    def run(self):
        self.build()

    def build(self):
        self.config.logger.debug('Starting build for {}:{}...'.format(self.project, self.version))

        build = self.config.api.start_build(self.project, self.version, self.mason_version)

        console_hostname = self.urlparse(self.config.endpoints_store['deploy_url']).hostname
        self.config.logger.info(inspect.cleandoc("""
            Build queued for OS Config '{0}'.
            You can see the status of your build at
            https://{1}/controller/projects/{0}
        """.format(self.project, console_hostname)))

        if self.block:
            self._wait_for_completion(build)

    def _wait_for_completion(self, build):
        self.config.logger.info('')

        # 40 minutes (*approximately* since this doesn't account for the request time)
        timeout_seconds = 40 * 60
        time_blocked = 0
        wait_time = 3
        while time_blocked < timeout_seconds:
            try:
                build = self.config.api.get_build(build.get('data').get('submittedAt'))
            except ApiError as e:
                self.config.logger.error(
                    "Build status check failed for OS Config '{}'.".format(self.project))
                raise e

            if build.get('data').get('status') == 'COMPLETED':
                self.config.logger.info("Build completed for OS Config '{}'.".format(self.project))
                return

            self.config.logger.info(
                "Waiting on build for OS Config '{}' to complete...".format(self.project))
            self.time.sleep(wait_time)

            time_blocked += wait_time
            wait_time = min(wait_time * 2, 60)

        self.config.logger.error(
            "Timed out waiting on build for OS Config '{}' to complete.".format(self.project))
        raise click.Abort()
