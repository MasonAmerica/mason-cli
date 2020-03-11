import os
import tempfile
import unittest

import yaml
from mock import MagicMock

from cli.internal.commands.init import InitCommand


class InitCommandTest(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()

    def test__config_rewrite__new_config_is_created_from_scratch(self):
        self.config.api.get_latest_artifact = MagicMock(return_value=None)
        command = InitCommand(self.config)

        config = command._rewritten_config('project-id')

        self.assertDictEqual(config, {
            'os': {
                'name': 'project-id',
                'version': 'latest'
            }
        })

    def test__config_rewrite__existing_config_is_updated(self):
        self.config.api.get_latest_artifact = MagicMock(return_value={
            'config': {
                'yo': True
            }
        })
        command = InitCommand(self.config)

        config = command._rewritten_config('project-id')

        self.assertDictEqual(config, {
            'yo': True,
            'os': {
                'name': 'project-id',
                'version': 'latest'
            }
        })

    def test__write__mason_rc_contains_config_file(self):
        working_dir = tempfile.mkdtemp()
        command = InitCommand(self.config, working_dir)

        command._write_files({}, [])

        with open(os.path.join(working_dir, '.masonrc')) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'configs': 'mason.yml',
            'apps': []
        })

    def test__write__mason_rc_contains_apps(self):
        working_dir = tempfile.mkdtemp()
        command = InitCommand(self.config, working_dir)

        command._write_files({}, ['a', 'b'])

        with open(os.path.join(working_dir, '.masonrc')) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'configs': 'mason.yml',
            'apps': ['a', 'b']
        })

    def test__write__config_file_is_written(self):
        working_dir = tempfile.mkdtemp()
        command = InitCommand(self.config, working_dir)

        command._write_files({'a': {'b': True}}, [])

        with open(os.path.join(working_dir, 'mason.yml')) as f:
            yml = yaml.safe_load(f)

        self.assertDictEqual(yml, {
            'a': {'b': True}
        })
