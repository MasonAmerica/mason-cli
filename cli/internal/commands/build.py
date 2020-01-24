import inspect

import click
import time

from cli.internal.commands.command import Command
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse


class BuildCommand(Command):
    def __init__(
        self,
        config,
        project,
        version,
        block,
        turbo,
        mason_version,
        time=time,
        urlparse=urlparse
    ):
        self.config = config
        self.project = project
        self.version = version
        self.block = block
        self.turbo = turbo
        self.mason_version = mason_version
        self.time = time
        self.urlparse = urlparse

        validate_credentials(config)

    def run(self):
        self.config.logger.debug('Starting build for {}:{}...'.format(self.project, self.version))

        try:
            build = self.config.api.start_build(
                self.project, self.version, self.turbo, self.mason_version)
        except ApiError as e:
            e.exit(self.config)
            return

        console_hostname = self.urlparse(self.config.endpoints_store['deploy_url']).hostname
        self.config.logger.info(inspect.cleandoc("""
            Build queued.
            You can see the status of your build at
            https://{}/controller/projects/{}
        """.format(console_hostname, self.project)))

        if self.block:
            self._wait_for_completion(build)

    def _wait_for_completion(self, build):
        self.config.logger.info('')

        # 40 minutes (*approximately* since this doesn't account for the request time)
        timeout_seconds = 40 * 60
        time_blocked = 0
        while time_blocked < timeout_seconds:
            try:
                build = self.config.api.get_build(build.get('data').get('submittedAt'))
            except ApiError as e:
                self.config.logger.error('Build status check failed.')
                e.exit(self.config)
                return

            if build.get('data').get('status') == 'COMPLETED':
                self.config.logger.info('Build completed.')
                return

            self.config.logger.info('Waiting for build to complete...')
            wait_time = 10 if self.turbo else 30
            self.time.sleep(wait_time)
            time_blocked += wait_time

        self.config.logger.error('Timed out waiting for build to complete.')
        raise click.Abort()
