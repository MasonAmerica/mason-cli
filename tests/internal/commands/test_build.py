import unittest

import click
from mock import MagicMock
from mock import call

from cli.internal.commands.build import BuildCommand
from cli.internal.utils.remote import ApiError


class BuildCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()

    def test_starts_build(self):
        command = BuildCommand(
            self.config, 'project-id', '1', False, False, None, urlparse=MagicMock())

        command.run()

        self.config.api.start_build.assert_called_with('project-id', '1', False, None)

    def test_failure_exits_cleanly(self):
        command = BuildCommand(self.config, 'project-id', '1', False, False, None)
        self.config.api.start_build = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_build_completion_awaits_successfully(self):
        def build_completer(id):
            if id == '1':
                return {'data': {'submittedAt': '2', 'status': 'PENDING'}}
            else:
                return {'data': {'status': 'COMPLETED'}}

        command = BuildCommand(
            self.config, 'project-id', '1', True, True, None, MagicMock(), MagicMock())
        self.config.api.start_build = MagicMock(return_value={'data': {'submittedAt': '1'}})
        self.config.api.get_build = MagicMock(side_effect=build_completer)

        command.run()

        self.config.api.start_build.assert_called_with('project-id', '1', True, None)
        self.config.api.get_build.assert_has_calls([call('1'), call('2')])

    def test_build_completion_exists_cleanly_on_failure(self):
        command = BuildCommand(
            self.config, 'project-id', '1', True, True, None, MagicMock(), MagicMock())
        self.config.api.start_build = MagicMock()
        self.config.api.get_build = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_build_completion_times_out_on_incomplete_build(self):
        command = BuildCommand(
            self.config, 'project-id', '1', True, True, None, MagicMock(), MagicMock())
        self.config.api.start_build = MagicMock(return_value={'data': {'submittedAt': '1'}})
        self.config.api.get_build = MagicMock(
            return_value={'data': {'submittedAt': '1', 'status': 'PENDING'}})

        with self.assertRaises(click.Abort):
            command.run()
