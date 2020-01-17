import unittest

from mock import MagicMock

from cli.internal.models.os_config import OSConfig


class ConfigTest(unittest.TestCase):
    def setUp(self):
        test_yaml = {
            'os': {
                'name': 'test',
                'version': 1
            }
        }

        self.test_config = OSConfig(MagicMock(), MagicMock(), test_yaml)

    def test_config_is_valid(self):
        self.assertIsNone(self.test_config.validate())

    def test_config_content_type(self):
        self.assertEqual(self.test_config.get_content_type(), 'text/x-yaml')

    def test_config_type(self):
        self.assertEqual(self.test_config.get_type(), 'config')

    def test_config_sub_type(self):
        self.assertIsNone(self.test_config.get_sub_type())

    def test_config_name(self):
        self.assertEqual(
            self.test_config.get_name(), str(self.test_config.ecosystem['os']['name']))

    def test_config_version(self):
        self.assertEqual(
            self.test_config.get_version(), str(self.test_config.ecosystem['os']['version']))

    def test_config_meta_data(self):
        self.assertIsNone(self.test_config.get_registry_meta_data())
