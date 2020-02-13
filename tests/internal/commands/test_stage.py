import os
import tempfile
import unittest

from mock import MagicMock

from cli.internal.commands.stage import StageCommand
from cli.internal.models.os_config import OSConfig
from tests import __tests_root__


class StageCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.endpoints_store.__getitem__ = MagicMock(return_value='https://google.com')

    def test_registers_and_uploads_config(self):
        input_config_file = os.path.join(__tests_root__, 'res/config.yml')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config.yml')
        command = StageCommand(self.config, [input_config_file], False, False, None, working_dir)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            config_file, OSConfig.parse(self.config, config_file))
        self.config.api.start_build.assert_called_with('project-id', '1', False, None)

    def test_registers_and_uploads_rewritten_config(self):
        self.config.api.get_latest_artifact = MagicMock(return_value={'version': '12'})
        self.config.api.get_highest_artifact = MagicMock(return_value={'version': '12'})
        input_config_file = os.path.join(__tests_root__, 'res/config4.yml')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config4.yml')
        command = StageCommand(self.config, [input_config_file], False, False, None, working_dir)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            config_file, OSConfig.parse(self.config, config_file))
        self.config.api.start_build.assert_called_with('project-id4', '13', False, None)
