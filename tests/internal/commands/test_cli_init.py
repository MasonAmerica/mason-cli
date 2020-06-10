import tempfile
import time
import unittest

from mock import MagicMock

from cli.internal.commands.cli_init import CliInitCommand
from cli.internal.utils.constants import UPDATE_CHECKER_CACHE
from cli.internal.utils.store import Store


class CliInitCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()

        self.current_time = time.time()
        fake_time = MagicMock()
        fake_time.time = MagicMock(side_effect=lambda: self.current_time)
        self.update_cache = Store('version-check-cache', {}, tempfile.mkdtemp(), False)
        self.update_cache._defaults = UPDATE_CHECKER_CACHE._defaults
        self.command = CliInitCommand(
            self.config,
            False, False, False, 'token', 'token', 'token',
            self.update_cache,
            fake_time)

    def test__update_check__old_version_is_ignored(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='0.0')

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['latest_version'], None)
        self.assertEqual(self.update_cache['last_nag_timestamp'], 0)
        self.assertEqual(self.update_cache['first_update_found_timestamp'], 0)

    def test__update_check__new_version_is_processed(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['latest_version'], '999.999.999')
        self.assertEqual(self.update_cache['last_nag_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['first_update_found_timestamp'], int(self.current_time))

    def test__update_check__request_is_cached(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()

        prev_time = self.current_time
        self.current_time = time.time()
        self.config.api = None

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(prev_time))
        self.assertEqual(self.update_cache['latest_version'], '999.999.999')
        self.assertEqual(self.update_cache['last_nag_timestamp'], int(prev_time))
        self.assertEqual(self.update_cache['first_update_found_timestamp'], int(prev_time))

    def test__update_check__user_is_nagged_using_cached_update_check(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()
        self.update_cache['update_check_frequency_seconds'] = 100000000000

        prev_time = self.current_time
        self.current_time = time.time() + 1000000

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(prev_time))
        self.assertEqual(self.update_cache['latest_version'], '999.999.999')
        self.assertEqual(self.update_cache['last_nag_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['first_update_found_timestamp'], int(prev_time))

    def test__update_check__first_update_timestamp_stick_through_multiple_updates(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()
        self.update_cache['update_check_frequency_seconds'] = 1

        self.config.api.get_latest_cli_version = MagicMock(return_value='1000.999.999')
        prev_time = self.current_time
        self.current_time = time.time() + 10

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['latest_version'], '1000.999.999')
        self.assertEqual(self.update_cache['last_nag_timestamp'], int(prev_time))
        self.assertEqual(self.update_cache['first_update_found_timestamp'], int(prev_time))

    def test__update_check__cache_gets_cleared_after_update(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()
        self.assertEqual(self.update_cache['current_version'], self.update_cache['runtime_version'])

        self.update_cache['runtime_version'] = '999.999.999'
        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['latest_version'], None)
        self.assertEqual(self.update_cache['current_version'], '999.999.999')
        self.assertEqual(self.update_cache['last_nag_timestamp'], 0)
        self.assertEqual(self.update_cache['first_update_found_timestamp'], 0)

    def test__update_check__cache_gets_cleared_after_rollback(self):
        self.config.api.get_latest_cli_version = MagicMock(return_value='999.999.999')

        self.command._check_for_updates()
        self.update_cache['update_check_frequency_seconds'] = 1

        self.config.api.get_latest_cli_version = MagicMock(return_value='0.0')
        self.current_time = time.time() + 10

        self.command._check_for_updates()

        self.assertEqual(self.update_cache['last_update_check_timestamp'], int(self.current_time))
        self.assertEqual(self.update_cache['latest_version'], None)
        self.assertEqual(self.update_cache['last_nag_timestamp'], 0)
        self.assertEqual(self.update_cache['first_update_found_timestamp'], 0)
