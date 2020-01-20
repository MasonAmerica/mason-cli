import os
import unittest

import click
from mock import MagicMock
from mock import call

from cli.internal.commands.register import RegisterApkCommand
from cli.internal.commands.register import RegisterConfigCommand
from cli.internal.commands.register import RegisterMediaCommand
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.remote import ApiError
from tests import __tests_root__


class RegisterCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.push = True
        self.config.no_https = False

    def test_registration_exits_cleanly_on_failure(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        command = RegisterConfigCommand(self.config, [config_file])
        self.config.api.upload_artifact = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_config_registers_successfully(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        command = RegisterConfigCommand(self.config, [config_file])

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            config_file, OSConfig.parse(self.config, config_file))

    def test_apk_registers_successfully(self):
        apk_file1 = os.path.join(__tests_root__, 'res/v1.apk')
        apk_file2 = os.path.join(__tests_root__, 'res/v1and2.apk')
        command = RegisterApkCommand(self.config, [apk_file1, apk_file2])

        command.run()

        self.config.api.upload_artifact.assert_has_calls([
            call(apk_file1, Apk.parse(self.config, apk_file1)),
            call(apk_file2, Apk.parse(self.config, apk_file2))
        ])

    def test_ota_registers_successfully(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        command = RegisterMediaCommand(self.config, 'Boot Anim', 'bootanimation', '1', media_file)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            media_file, Media.parse(self.config, 'Boot anim', 'bootanimation', '1', media_file))
