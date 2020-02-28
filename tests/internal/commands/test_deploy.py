import unittest
from concurrent.futures.thread import ThreadPoolExecutor

import click
from mock import MagicMock
from mock import call

from cli.internal.commands.deploy import DeployApkCommand
from cli.internal.commands.deploy import DeployConfigCommand
from cli.internal.commands.deploy import DeployOtaCommand
from cli.internal.utils.remote import ApiError


class DeployCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.push = True
        self.config.no_https = False
        self.config.executor = ThreadPoolExecutor()

    def test_deployment_exits_cleanly_on_failure(self):
        command = DeployConfigCommand(self.config, 'project-id', '1', ['group1', 'group2'])
        self.config.api.deploy_artifact = MagicMock(side_effect=ApiError())

        with self.assertRaises(click.Abort):
            command.run()

    def test_non_existent_latest_config_fails(self):
        self.config.api.get_latest_artifact = MagicMock(return_value=None)
        command = DeployConfigCommand(self.config, 'project-id', 'latest', ['group1', 'group2'])

        with self.assertRaises(click.Abort):
            command.run()

    def test_config_deploys_successfully(self):
        command = DeployConfigCommand(self.config, 'project-id', '1', ['group1', 'group2'])

        command.run()

        self.config.api.deploy_artifact.assert_has_calls([
            call('config', 'project-id', '1', 'group1', True, False),
            call('config', 'project-id', '1', 'group2', True, False)
        ], any_order=True)

    def test_latest_config_deploys_successfully(self):
        self.config.api.get_latest_artifact = MagicMock(return_value={'version': '42'})
        command = DeployConfigCommand(self.config, 'project-id', 'latest', ['group1', 'group2'])

        command.run()

        self.config.api.deploy_artifact.assert_has_calls([
            call('config', 'project-id', '42', 'group1', True, False),
            call('config', 'project-id', '42', 'group2', True, False)
        ], any_order=True)

    def test_non_existent_latest_apk_fails(self):
        self.config.api.get_latest_artifact = MagicMock(return_value=None)
        command = DeployApkCommand(self.config, 'com.example.app', 'latest', ['group1', 'group2'])

        with self.assertRaises(click.Abort):
            command.run()

    def test_apk_deploys_successfully(self):
        command = DeployApkCommand(self.config, 'com.example.app', '1', ['group1', 'group2'])

        command.run()

        self.config.api.deploy_artifact.assert_has_calls([
            call('apk', 'com.example.app', '1', 'group1', True, False),
            call('apk', 'com.example.app', '1', 'group2', True, False)
        ], any_order=True)

    def test_latest_apk_deploys_successfully(self):
        self.config.api.get_latest_artifact = MagicMock(return_value={'version': '42'})
        command = DeployApkCommand(self.config, 'com.example.app', 'latest', ['group1', 'group2'])

        command.run()

        self.config.api.deploy_artifact.assert_has_calls([
            call('apk', 'com.example.app', '42', 'group1', True, False),
            call('apk', 'com.example.app', '42', 'group2', True, False)
        ], any_order=True)

    def test_ota_deploys_successfully(self):
        command = DeployOtaCommand(self.config, 'mason-os', '1', ['group1', 'group2'])

        command.run()

        self.config.api.deploy_artifact.assert_has_calls([
            call('ota', 'mason-os', '1', 'group1', True, False),
            call('ota', 'mason-os', '1', 'group2', True, False)
        ], any_order=True)
