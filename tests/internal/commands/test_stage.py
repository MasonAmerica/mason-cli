import os
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
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        command = StageCommand(self.config, [config_file], False, False, None)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            config_file, OSConfig.parse(self.config, config_file))
        self.config.api.start_build.assert_called_with('project-id', '1', False, None)
