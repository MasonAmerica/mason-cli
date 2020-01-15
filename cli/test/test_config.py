import unittest

from test_common import Common

from cli.internal.os_config import OSConfig


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.test_config = self._create_test_config()

    def test_config_is_valid(self):
        self.test_config.validate()

    def test_config_content_type(self):
        assert(self.test_config.get_content_type() == 'text/x-yaml')

    def test_config_type(self):
        assert(self.test_config.get_type() == 'config')

    def test_config_sub_type(self):
        assert(self.test_config.get_sub_type() is None)

    def test_config_name(self):
        assert(self.test_config.get_name() == str(self.test_config.ecosystem['os']['name']))

    def test_config_version(self):
        assert(self.test_config.get_version() == str(self.test_config.ecosystem['os']['version']))

    def test_config_meta_data(self):
        assert(self.test_config.get_registry_meta_data() is None)

    @staticmethod
    def _create_test_config():
        test_config = Common.create_mock_config()
        test_yaml = Common.create_config_file()
        return OSConfig(test_config, test_yaml)
