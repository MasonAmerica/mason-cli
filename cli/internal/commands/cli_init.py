import inspect
import time

import click_log
import packaging.version
import requests

from cli.config import Config
from cli.internal.commands.command import Command
from cli.internal.utils.store import Store
from cli.version import __version__


class CliInitCommand(Command):
    def __init__(
        self,
        config: Config,
        debug: bool,
        verbose: bool,
        no_color: bool,
        api_key: str,
        id_token: str,
        access_token: str
    ):
        super(CliInitCommand, self).__init__(config)

        self.debug = debug
        self.verbose = verbose
        self.no_color = no_color
        self.api_key = api_key
        self.id_token = id_token
        self.access_token = access_token

    @Command.helper('cli')
    def run(self):
        self._update_logging()
        self._update_creds()
        self._check_for_updates()

    def _update_logging(self):
        if self.no_color:
            click_log.ColorFormatter.colors = {
                'error': {},
                'exception': {},
                'critical': {},
                'debug': {},
                'warning': {}
            }

        if self.verbose or self.debug:
            self.config.logger.warning('--debug and --verbose options are deprecated. Please use '
                                       '--verbosity debug instead.')
            self.config.logger.setLevel('DEBUG')

        self.config.logger.log(1, 'Lowest logging level activated.')
        self.config.logger.debug('Debug logging activated.')

    def _update_creds(self):
        if self.api_key:
            self.config.auth_store['api_key'] = self.api_key
        if self.id_token:
            self.config.auth_store['id_token'] = self.id_token
        if self.access_token:
            self.config.auth_store['access_token'] = self.access_token

        if self.id_token or self.access_token:
            self.config.logger.warning(
                'The --id-token and --access-token options are deprecated. Please '
                'use --api-key instead.')

    def _check_for_updates(self):
        current_time = int(time.time())
        cache = Store('version-check-cache', {'timestamp': 0})

        if current_time - cache['timestamp'] < 86400:  # 1 day
            self.config.logger.debug('Skipped version check')
            return
        cache['timestamp'] = current_time
        cache.save()

        self.config.logger.debug('Checking for updates')
        try:
            r = requests.get(self.config.endpoints_store['latest_version_url'])
        except requests.RequestException as e:
            # Don't fail the command if checking for updates fails.
            self.config.logger.debug(e)
            return

        if r.status_code == 200 and r.text:
            current_version = packaging.version.parse(__version__)
            remote_version = packaging.version.parse(r.text)
            if remote_version > current_version:
                self.config.logger.info(inspect.cleandoc("""
                    ==================== NOTICE ====================
                    A newer version (v{}) of the Mason CLI is available.

                    Download the latest version:
                    https://github.com/MasonAmerica/mason-cli/releases/latest

                    And check out our installation guide:
                    http://docs.bymason.com/mason-cli/#install
                    ==================== NOTICE ====================
                """.format(remote_version)))
                self.config.logger.info('')
        else:
            self.config.logger.debug('Failed to check for updates: {}'.format(r))
