import inspect
import time
from math import e

import click_log
import packaging.version

from cli.config import Config
from cli.config import register_manual_atexit_callback
from cli.internal.commands.command import Command
from cli.internal.utils.constants import UPDATE_CHECKER_CACHE
from cli.internal.utils.io import wait_for_futures
from cli.internal.utils.remote import ApiError
from cli.internal.utils.store import Store


class CliInitCommand(Command):
    def __init__(
        self,
        config: Config,
        debug: bool,
        verbose: bool,
        no_color: bool,
        api_key: str,
        id_token: str,
        access_token: str,
        update_checker_cache: Store = UPDATE_CHECKER_CACHE,
        time=time
    ):
        super(CliInitCommand, self).__init__(config)

        self.debug = debug
        self.verbose = verbose
        self.no_color = no_color
        self.api_key = api_key
        self.id_token = id_token
        self.access_token = access_token
        self.update_checker_cache = update_checker_cache
        self.time = time

    @Command.helper('cli')
    def run(self):
        self._update_logging()
        self._update_creds()
        update_check_future = self.config.executor.submit(self._check_for_updates)
        register_manual_atexit_callback(
            wait_for_futures, self.config.executor, [update_check_future])

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
        cache = self.update_checker_cache

        runtime_version = cache['runtime_version']
        if 'current_version' not in cache or not cache['current_version'] == runtime_version:
            # Fresh install or update installed. Either way, we want to start with fresh state to
            # clear out old schemas.
            cache.clear()
            cache['current_version'] = runtime_version

        current_version = cache['current_version']
        current_time = int(self.time.time())
        frequency = cache['update_check_frequency_seconds']

        if current_time - cache['last_update_check_timestamp'] >= frequency:
            available_update, success = self._get_available_update(current_version)
            if success:
                cache['last_update_check_timestamp'] = current_time
                cache['latest_version'] = available_update

                first_timestamp = cache['first_update_found_timestamp']
                if available_update:
                    first_timestamp = first_timestamp or current_time
                else:
                    first_timestamp = None
                    cache['last_nag_timestamp'] = None
                cache['first_update_found_timestamp'] = first_timestamp
        else:
            available_update = cache['latest_version']

        if not available_update:
            cache.save()
            return

        if not self._compare_versions(current_version, available_update):
            cache['latest_version'] = None
            cache['last_nag_timestamp'] = None
            cache['first_update_found_timestamp'] = None
            cache.save()
            return

        should_nag = self._should_nag_user_about_update(
            current_time, cache['last_nag_timestamp'], cache['first_update_found_timestamp'])
        if should_nag:
            cache['last_nag_timestamp'] = current_time
            register_manual_atexit_callback(self._nag_user_about_update, available_update)

        cache.save()

    def _get_available_update(self, current):
        try:
            latest_version = self.config.api.get_latest_cli_version()
            return self._compare_versions(current, latest_version), True
        except ApiError as e:
            # Don't fail the command if checking for updates fails.
            self.config.logger.debug(e.message)
            return None, False

    def _compare_versions(self, current, new):
        current_version = packaging.version.parse(current)
        new_version = packaging.version.parse(new)

        if new_version > current_version:
            return str(new_version)

    def _should_nag_user_about_update(
        self,
        current_time,
        last_nag_timestamp,
        first_update_found_timestamp
    ):
        days_since_update_found = (current_time - first_update_found_timestamp) / 86400
        seconds_since_last_nag = current_time - last_nag_timestamp

        nag_timeout = 86400 / (1 + e ** min(25, .4 * days_since_update_found - 5))
        if seconds_since_last_nag >= nag_timeout:
            return True

    def _nag_user_about_update(self, version):
        self.config.logger.info('')
        self.config.logger.info(inspect.cleandoc("""
            ==================== NOTICE ====================
            A newer version (v{}) of the Mason CLI is available.

            Download the latest version:
            https://github.com/MasonAmerica/mason-cli/releases/latest

            And check out our installation guide:
            http://docs.bymason.com/mason-cli/#install
            ==================== NOTICE ====================
        """.format(version)))
