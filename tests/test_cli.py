import inspect
import os
import unittest

from click.testing import CliRunner
from mock import MagicMock

from cli import __version__
from cli.internal.utils.store import Store
from cli.mason import Config
from cli.mason import cli
from tests import __tests_root__


class CliTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test__version__command_prints_info(self):
        result = self.runner.invoke(cli, ['version'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Mason CLI v{}
            Copyright (C) 2019 Mason America (https://bymason.com)
            License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>
        """.format(__version__)))

    def test__version__V_flag_prints_info(self):
        result = self.runner.invoke(cli, ['-V'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Mason CLI v{}
            Copyright (C) 2019 Mason America (https://bymason.com)
            License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>
        """.format(__version__)))

    def test__version__version_option_prints_info(self):
        result = self.runner.invoke(cli, ['--version'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Mason CLI v{}
            Copyright (C) 2019 Mason America (https://bymason.com)
            License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>
        """.format(__version__)))

    def test__logging__starts_at_info_level_by_default(self):
        result = self.runner.invoke(cli, ['version'])

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn('Lowest logging level activated.', result.output)
        self.assertNotIn('debug: Debug logging activated.', result.output)

    def test__logging__switching_to_debug_level_logs_debug_messages(self):
        result = self.runner.invoke(cli, ['-v', 'debug', 'version'])

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn('Lowest logging level activated.', result.output)
        self.assertIn('debug: Debug logging activated.', result.output)

    def test__logging__switching_to_custom_level_logs_custom_messages(self):
        result = self.runner.invoke(cli, ['-v', '1', 'version'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Lowest logging level activated.', result.output)
        self.assertIn('debug: Debug logging activated.', result.output)

    def test__logging__switching_to_debug_level_through_env_var_logs_debug_messages(self):
        os.environ['LOGLEVEL'] = 'DEBUG'
        result = self.runner.invoke(cli, ['version'])
        del os.environ['LOGLEVEL']

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn('Lowest logging level activated.', result.output)
        self.assertIn('debug: Debug logging activated.', result.output)

    def test__logging__switching_to_custom_level_through_env_var_logs_custom_messages(self):
        os.environ['LOGLEVEL'] = '1'
        result = self.runner.invoke(cli, ['version'])
        del os.environ['LOGLEVEL']

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Lowest logging level activated.', result.output)
        self.assertIn('debug: Debug logging activated.', result.output)

    def test__logging__colors_are_enabled_by_default(self):
        result = self.runner.invoke(cli, ['-v', 'debug', 'version'], color=True)

        self.assertEqual(result.exit_code, 0)
        self.assertIn(b'\x1b[34mdebug: \x1b[0mDebug logging activated.', result.stdout_bytes)

    def test__logging__colors_can_be_disabled(self):
        result = self.runner.invoke(cli, ['-v', 'debug', '--no-color', 'version'], color=True)

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn(b'\x1b[34mdebug: \x1b[0mDebug logging activated.', result.stdout_bytes)

    def test__cli__default_creds_are_retrieved_from_disk(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)
            auth_store['api_key'] = 'Foobar'
        config = Config(auth_store=auth_store)

        result = self.runner.invoke(cli, ['version'], obj=config)

        self.assertEqual(result.exit_code, 0)

        self.assertDictEqual(auth_store._fields, {'api_key': 'Foobar'})

    def test__cli__api_key_option_updates_creds(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)
            auth_store['api_key'] = 'Foobar'
        config = Config(auth_store=auth_store)

        result = self.runner.invoke(cli, ['--token', 'New foobar', 'version'], obj=config)

        self.assertEqual(result.exit_code, 0)

        self.assertDictEqual(auth_store._fields, {'api_key': 'New foobar'})
        auth_store.clear()
        auth_store.restore()
        self.assertDictEqual(auth_store._fields, {})

    def test__register_config__no_files_fails(self):
        result = self.runner.invoke(cli, ['register', 'config'])

        self.assertEqual(result.exit_code, 2)

    def test__register_config__non_existent_file_fails(self):
        result = self.runner.invoke(cli, ['register', 'config', 'foobar'])

        self.assertEqual(result.exit_code, 2)

    def test__register_config__no_creds_fails(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'config', config_file], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__register_config__negative_confirmation_aborts(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'config', config_file], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            --------- OS Config ---------
            File Name: {}
            File size: 190
            Name: project-id
            Version: 1
            -----------------------------
            Continue register? [Y/n]: n
            Aborted!
        """.format(config_file)))

    def test__register_config__file_is_registered(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'config', config_file], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            --------- OS Config ---------
            File Name: {}
            File size: 190
            Name: project-id
            Version: 1
            -----------------------------
            Continue register? [Y/n]: 
            Artifact registered.
        """.format(config_file)))

    def test__register_apk__no_files_fails(self):
        result = self.runner.invoke(cli, ['register', 'apk'])

        self.assertEqual(result.exit_code, 2)

    def test__register_apk__non_existent_file_fails(self):
        result = self.runner.invoke(cli, ['register', 'apk', 'foobar'])

        self.assertEqual(result.exit_code, 2)

    def test__register_apk__no_creds_fails(self):
        apk_file = os.path.join(__tests_root__, 'res/v1.apk')
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'apk', apk_file], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__register_apk__negative_confirmation_aborts(self):
        apk_file = os.path.join(__tests_root__, 'res/v1.apk')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'apk', apk_file], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ------------ APK ------------
            File Name: {}
            File size: 1319297
            Package: com.example.unittestapp1
            Version Name: 1.0
            Version Code: 1
            -----------------------------
            Continue register? [Y/n]: n
            Aborted!
        """.format(apk_file)))

    def test__register_apk__file_is_registered(self):
        apk_file = os.path.join(__tests_root__, 'res/v1.apk')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['register', 'apk', apk_file], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ------------ APK ------------
            File Name: {}
            File size: 1319297
            Package: com.example.unittestapp1
            Version Name: 1.0
            Version Code: 1
            -----------------------------
            Continue register? [Y/n]: 
            Artifact registered.
        """.format(apk_file)))

    def test__register_media__no_files_fails(self):
        result = self.runner.invoke(cli, ['register', 'media'])

        self.assertEqual(result.exit_code, 2)

    def test__register_media__non_existent_file_fails(self):
        result = self.runner.invoke(
            cli, ['register', 'media', 'bootanimation', 'Anim name', '1', 'foobar'])

        self.assertEqual(result.exit_code, 1)

    def test__register_media__invalid_media_type_fails(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        result = self.runner.invoke(
            cli, ['register', 'media', 'invalid', 'Anim name', '1', media_file])

        self.assertEqual(result.exit_code, 1)

    def test__register_media__invalid_version_fails(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        result = self.runner.invoke(
            cli, ['register', 'media', 'bootanimation', 'Anim name', 'invalid', media_file])

        self.assertEqual(result.exit_code, 1)

    def test__register_media__no_creds_fails(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'register', 'media',
            'bootanimation', 'Anim name', '1', media_file
        ], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__register_media__negative_confirmation_aborts(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'register', 'media',
            'bootanimation', 'Anim name', '1', media_file
        ], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ----------- MEDIA -----------
            File Name: {}
            File size: 3156136
            Name: Anim name
            Version: 1
            Type: bootanimation
            -----------------------------
            Continue register? [Y/n]: n
            Aborted!
        """.format(media_file)))

    def test__register_media__file_is_registered(self):
        media_file = os.path.join(__tests_root__, 'res/bootanimation.zip')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'register', 'media',
            'bootanimation', 'Anim name', '1', media_file
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ----------- MEDIA -----------
            File Name: {}
            File size: 3156136
            Name: Anim name
            Version: 1
            Type: bootanimation
            -----------------------------
            Continue register? [Y/n]: 
            Artifact registered.
        """.format(media_file)))

    def test__build__invalid_version_fails(self):
        result = self.runner.invoke(cli, ['build', 'project-id', 'invalid'])

        self.assertEqual(result.exit_code, 2)

    def test__build__no_creds_fails(self):
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['build', 'project-id', '1'], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__build__build_is_started(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['build', 'project-id', '1'], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Build queued.
            You can see the status of your build at
            https://platform.bymason.com/controller/projects/project-id
        """))

    def test__build__build_is_started_and_awaited_for_completion(self):
        api = MagicMock()
        api.get_build = MagicMock(return_value={'data': {'status': 'COMPLETED'}})
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['build', '--await', 'project-id', '1'], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Build queued.
            You can see the status of your build at
            https://platform.bymason.com/controller/projects/project-id

            Build completed.
        """))

    def test__stage__no_files_fails(self):
        result = self.runner.invoke(cli, ['stage'])

        self.assertEqual(result.exit_code, 2)

    def test__stage__non_existent_file_fails(self):
        result = self.runner.invoke(cli, ['stage', 'foobar'])

        self.assertEqual(result.exit_code, 2)

    def test__stage__no_creds_fails(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['stage', config_file], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__stage__negative_confirmation_aborts(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['stage', config_file], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            --------- OS Config ---------
            File Name: {}
            File size: 190
            Name: project-id
            Version: 1
            -----------------------------
            Continue register? [Y/n]: n
            Aborted!
        """.format(config_file)))

    def test__stage__file_is_registered(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['stage', config_file], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            --------- OS Config ---------
            File Name: {}
            File size: 190
            Name: project-id
            Version: 1
            -----------------------------
            Continue register? [Y/n]: 
            Artifact registered.

            Build queued.
            You can see the status of your build at
            https://platform.bymason.com/controller/projects/project-id
        """.format(config_file)))

    def test__stage__config_is_registered_and_awaits_build_completion(self):
        config_file = os.path.join(__tests_root__, 'res/config.yml')
        api = MagicMock()
        api.get_build = MagicMock(return_value={'data': {'status': 'COMPLETED'}})
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, ['stage', '--await', config_file], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            --------- OS Config ---------
            File Name: {}
            File size: 190
            Name: project-id
            Version: 1
            -----------------------------
            Continue register? [Y/n]: 
            Artifact registered.

            Build queued.
            You can see the status of your build at
            https://platform.bymason.com/controller/projects/project-id

            Build completed.
        """.format(config_file)))

    def test__deploy_config__invalid_name_fails(self):
        result = self.runner.invoke(cli, ['deploy', 'config', 'project-id', 'invalid', 'group'])

        self.assertEqual(result.exit_code, 2)

    def test__deploy_config__no_group_fails(self):
        result = self.runner.invoke(cli, ['deploy', 'config', 'project-id', '1'])

        self.assertEqual(result.exit_code, 2)

    def test__deploy_config__no_creds_fails(self):
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'config',
            'project-id', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__deploy_config__negative_confirmation_aborts(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'config',
            'project-id', '1', 'group'
        ], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: project-id
            Type: config
            Version: 1
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: n
            Aborted!
        """))

    def test__deploy_config__config_is_deployed(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'config',
            'project-id', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: project-id
            Type: config
            Version: 1
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_config__warning_is_logged_when_no_https_flag_is_used(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', '--no-https', 'config',
            'project-id', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: project-id
            Type: config
            Version: 1
            Group: group
            Push: False
    
            ***WARNING***
            --no-https enabled: this deployment will be delivered to devices over HTTP.
            ***WARNING***
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_apk__invalid_name_fails(self):
        result = self.runner.invoke(cli, ['deploy', 'apk', 'com.example.app', 'invalid', 'group'])

        self.assertEqual(result.exit_code, 2)

    def test__deploy_apk__no_group_fails(self):
        result = self.runner.invoke(cli, ['deploy', 'apk', 'com.example.app', '1'])

        self.assertEqual(result.exit_code, 2)

    def test__deploy_apk__no_creds_fails(self):
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'apk',
            'com.example.app', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__deploy_apk__negative_confirmation_aborts(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'apk',
            'com.example.app', '1', 'group'
        ], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: com.example.app
            Type: apk
            Version: 1
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: n
            Aborted!
        """))

    def test__deploy_apk__config_is_deployed(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'apk',
            'com.example.app', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: com.example.app
            Type: apk
            Version: 1
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_apk__warning_is_logged_when_no_https_flag_is_used(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', '--no-https', 'apk',
            'com.example.app', '1', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: com.example.app
            Type: apk
            Version: 1
            Group: group
            Push: False
    
            ***WARNING***
            --no-https enabled: this deployment will be delivered to devices over HTTP.
            ***WARNING***
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_ota__no_group_fails(self):
        result = self.runner.invoke(cli, ['deploy', 'ota', 'mason-os', '1'])

        self.assertEqual(result.exit_code, 2)

    def test__deploy_ota__no_creds_fails(self):
        api = MagicMock()
        config = Config(auth_store=self._uninitialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'ota',
            'mason-os', '2.0.0', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            error: Not authenticated. Run 'mason login' to sign in.
            Aborted!
        """))

    def test__deploy_ota__negative_confirmation_aborts(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'ota',
            'mason-os', '2.0.0', 'group'
        ], obj=config, input='n')

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: mason-os
            Type: ota
            Version: 2.0.0
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: n
            Aborted!
        """))

    def test__deploy_ota__config_is_deployed(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', 'ota',
            'mason-os', '2.0.0', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: mason-os
            Type: ota
            Version: 2.0.0
            Group: group
            Push: False
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_ota__warning_is_logged_when_no_https_flag_is_used(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', '--no-https', 'ota',
            'mason-os', '2.0.0', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            ---------- DEPLOY -----------
            Name: mason-os
            Type: ota
            Version: 2.0.0
            Group: group
            Push: False
    
            ***WARNING***
            --no-https enabled: this deployment will be delivered to devices over HTTP.
            ***WARNING***
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__deploy_ota__warning_is_logged_when_invalid_name(self):
        api = MagicMock()
        config = Config(auth_store=self._initialized_auth_store(), api=api)

        result = self.runner.invoke(cli, [
            'deploy', '--no-https', 'ota',
            'invalid', '2.0.0', 'group'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            warning: Unknown name 'invalid' for 'ota' deployments. Forcing it to 'mason-os'
            ---------- DEPLOY -----------
            Name: mason-os
            Type: ota
            Version: 2.0.0
            Group: group
            Push: False
    
            ***WARNING***
            --no-https enabled: this deployment will be delivered to devices over HTTP.
            ***WARNING***
            -----------------------------
            Continue deploy? [Y/n]: 
            Artifact deployed.
        """))

    def test__login__saves_creds(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)
        api = MagicMock()
        api.login = MagicMock(return_value={'id_token': 'id', 'access_token': 'access'})
        config = Config(auth_store=auth_store, api=api)

        result = self.runner.invoke(cli, [
            'login',
            '--token', 'Foobar',
            '--username', 'name',
            '--password', 'pass'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Successfully logged in.
        """.format(__version__)))

        auth_store.clear()
        auth_store.restore()
        self.assertDictEqual(auth_store._fields, {
            'api_key': 'Foobar',
            'id_token': 'id',
            'access_token': 'access'
        })

    def test__login__empty_api_key_is_ignored(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)
            auth_store['api_key'] = 'Foobar'
            auth_store.save()
        api = MagicMock()
        api.login = MagicMock(return_value={'id_token': 'id', 'access_token': 'access'})
        config = Config(auth_store=auth_store, api=api)

        result = self.runner.invoke(cli, [
            'login',
            '--username', 'name',
            '--password', 'pass'
        ], obj=config)

        self.assertEqual(result.exit_code, 0)

        auth_store.clear()
        auth_store.restore()
        self.assertDictEqual(auth_store._fields, {
            'api_key': 'Foobar',
            'id_token': 'id',
            'access_token': 'access'
        })

    def test__logout__clears_creds(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)
            auth_store['apk_key'] = 'Foobar'
            auth_store.save()
        config = Config(auth_store=auth_store)

        result = self.runner.invoke(cli, ['logout'], obj=config)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(inspect.cleandoc(result.output), inspect.cleandoc("""
            Successfully logged out.
        """.format(__version__)))

        auth_store.restore()
        self.assertIsNone(auth_store['apk_key'])

    def _uninitialized_auth_store(self):
        with self.runner.isolated_filesystem():
            return Store('fake-auth', {}, os.path.abspath(''), False)

    def _initialized_auth_store(self):
        with self.runner.isolated_filesystem():
            auth_store = Store('fake-auth', {}, os.path.abspath(''), False)

            auth_store['api_key'] = 'key'
            auth_store['id_token'] = 'id'
            auth_store['access_token'] = 'access'

            return auth_store
