import os
import tempfile
import unittest
from concurrent.futures.thread import ThreadPoolExecutor

import click
import yaml
from mock import MagicMock
from mock import call

from cli.internal.commands.register import RegisterApkCommand
from cli.internal.commands.register import RegisterConfigCommand
from cli.internal.commands.register import RegisterMediaCommand
from cli.internal.commands.register import RegisterProjectCommand
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.remote import ApiError
from tests import __tests_root__


class RegisterCommandTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        self.config = MagicMock()
        self.config.push = True
        self.config.no_https = False
        self.config.executor = ThreadPoolExecutor()

    def test_registration_exits_cleanly_on_failure(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        command = RegisterConfigCommand(self.config, [config_file])
        self.config.api.upload_artifact = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_registration_with_rewrite_exits_cleanly_on_failure(self):
        config_file = os.path.join(__tests_root__, 'res/config3.yml')
        command = RegisterConfigCommand(self.config, [config_file])
        self.config.api.get_latest_artifact = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_config_registers_successfully(self):
        input_config_file = os.path.join(__tests_root__, 'res/config.yml')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config.yml')
        command = RegisterConfigCommand(self.config, [input_config_file], working_dir)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            config_file, OSConfig.parse(self.config, config_file))

    def test_config_registers_rewritten_config_successfully(self):
        self.config.api.get_latest_artifact = MagicMock(return_value={'version': '41'})
        self.config.api.get_highest_artifact = MagicMock(return_value={'version': '41'})
        input_config_file = os.path.join(__tests_root__, 'res/config4.yml')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config4.yml')
        command = RegisterConfigCommand(self.config, [input_config_file], working_dir)

        command.run()
        with open(config_file) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'os': {
                'name': 'project-id4',
                'version': 42,
                'configurations': {'mason-management': {'disable_keyguard': True}}
            },
            'apps': [{
                'name': 'Testy Testeron',
                'package_name': 'com.example.app1',
                'version_code': 1
            }, {
                'name': 'Testy Testeron',
                'package_name': 'com.example.app2',
                'version_code': 41
            }],
            'media': {
                'bootanimation': {
                    'name': 'anim',
                    'version': 41
                }
            }
        })

    def test_config_registers_new_rewritten_config_successfully(self):
        # noinspection PyUnusedLocal
        def version_finder(name, type):
            if type == 'apk' or type == 'media':
                return {'version': '12'}

        self.config.api.get_latest_artifact = MagicMock(side_effect=version_finder)
        self.config.api.get_highest_artifact = MagicMock(side_effect=version_finder)
        input_config_file = os.path.join(__tests_root__, 'res/config4.yml')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config4.yml')
        command = RegisterConfigCommand(self.config, [input_config_file], working_dir)

        command.run()
        with open(config_file) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'os': {
                'name': 'project-id4',
                'version': 1,
                'configurations': {'mason-management': {'disable_keyguard': True}}
            },
            'apps': [{
                'name': 'Testy Testeron',
                'package_name': 'com.example.app1',
                'version_code': 1
            }, {
                'name': 'Testy Testeron',
                'package_name': 'com.example.app2',
                'version_code': 12
            }],
            'media': {
                'bootanimation': {
                    'name': 'anim',
                    'version': 12
                }
            }
        })

    def test_apk_registers_successfully(self):
        apk_file1 = os.path.join(__tests_root__, 'res/v1.apk')
        apk_file2 = os.path.join(__tests_root__, 'res/v1and2.apk')
        command = RegisterApkCommand(self.config, [apk_file1, apk_file2])

        command.run()

        self.config.api.upload_artifact.assert_has_calls([
            call(apk_file1, Apk.parse(self.config, apk_file1)),
            call(apk_file2, Apk.parse(self.config, apk_file2))
        ], any_order=True)

    def test_media_registers_successfully(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        command = RegisterMediaCommand(self.config, 'Boot Anim', 'bootanimation', '1', media_file)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            media_file, Media.parse(self.config, 'Boot anim', 'bootanimation', '1', media_file))

    def test_latest_media_registers_successfully(self):
        self.config.api.get_highest_artifact = MagicMock(return_value={'version': '41'})
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        command = RegisterMediaCommand(
            self.config, 'Boot Anim', 'bootanimation', 'latest', media_file)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            media_file, Media.parse(self.config, 'Boot anim', 'bootanimation', '42', media_file))

    def test_latest_non_existant_media_registers_successfully(self):
        self.config.api.get_highest_artifact = MagicMock(return_value=None)
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        command = RegisterMediaCommand(
            self.config, 'Boot Anim', 'bootanimation', 'latest', media_file)

        command.run()

        self.config.api.upload_artifact.assert_called_with(
            media_file, Media.parse(self.config, 'Boot anim', 'bootanimation', '1', media_file))

    def test_project_registers_successfully(self):
        self.config.endpoints_store.__getitem__ = MagicMock(return_value='https://google.com')
        self.config.api.get_build = MagicMock(return_value={'data': {'status': 'COMPLETED'}})
        simple_project = os.path.join(__tests_root__, 'res/simple-project')
        apk_file = os.path.join(__tests_root__, 'res/simple-project/v1.apk')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'mason.yml')
        command = RegisterProjectCommand(self.config, simple_project, working_dir)

        command.run()

        self.config.api.upload_artifact.assert_has_calls([
            call(apk_file, Apk.parse(self.config, apk_file)),
            call(config_file, OSConfig.parse(self.config, config_file))
        ])
        self.config.api.start_build.assert_called_with('project-id2', '2', True, None)

    def test_project_registers_updated_config(self):
        self.config.endpoints_store.__getitem__ = MagicMock(return_value='https://google.com')
        self.config.api.get_build = MagicMock(return_value={'data': {'status': 'COMPLETED'}})
        simple_project = os.path.join(__tests_root__, 'res/simple-project')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'mason.yml')
        command = RegisterProjectCommand(self.config, simple_project, working_dir)

        command.run()
        with open(config_file) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'os': {
                'name': 'project-id2',
                'version': 2,
                'configurations': {'mason-management': {'disable_keyguard': True}}
            },
            'apps': [{
                'name': 'Dummy app',
                'package_name': 'com.example.unittestapp1',
                'version_code': 1
            }]
        })

    def test_project_registers_updated_complex_config(self):
        self.config.endpoints_store.__getitem__ = MagicMock(return_value='https://google.com')
        self.config.api.get_build = MagicMock(return_value={'data': {'status': 'COMPLETED'}})
        self.config.api.get_latest_artifact = MagicMock(return_value={'version': '41'})
        self.config.api.get_highest_artifact = MagicMock(return_value={'version': '41'})
        complex_project = os.path.join(__tests_root__, 'res/complex-project')
        working_dir = tempfile.mkdtemp()
        config_file = os.path.join(working_dir, 'config3.yml')
        command = RegisterProjectCommand(self.config, complex_project, working_dir)

        command.run()
        with open(config_file) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'os': {
                'name': 'project-id3',
                'version': 42,
                'configurations': {'mason-management': {'disable_keyguard': True}}
            },
            'apps': [{
                'name': 'Testy Testeron',
                'package_name': 'com.example.app1',
                'version_code': 1
            }, {
                'name': 'Dummy app',
                'package_name': 'com.example.unittestapp1',
                'version_code': 1
            }, {
                'name': 'Testy Testeron',
                'package_name': 'com.example.app2',
                'version_code': 41
            }],
            'media': {
                'bootanimation': {
                    'name': 'anim-1',
                    'version': 42
                }
            }
        })
