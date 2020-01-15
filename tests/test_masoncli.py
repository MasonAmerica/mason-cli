# COPYRIGHT MASONAMERICA
import unittest

from mock import MagicMock

from cli.internal.masoncli import MasonCli
from tests.common import Common


class MasonTest(unittest.TestCase):

    def setUp(self):
        config = Common.create_mock_config()
        api_mock = MagicMock()
        cli = MasonCli(config)
        cli.api = api_mock

        self.mason = cli
        self.api_mock = api_mock

    def test_register_apk(self):
        self.mason.set_access_token("foo")
        self.mason.set_id_token("bar")

        apkf = "tests/res/v1.apk"
        self.mason.register_apk(apkf)

        self.api_mock.upload_artifact.assert_called_with(apkf, self.mason.artifact)

    def test_build_project(self):
        self.mason.set_access_token("foo")
        self.mason.set_id_token("bar")

        test_project = 'TestProjectName'
        test_version = '1.3.2.5.2.13.6'
        test_fast_build = False

        self.mason.build(test_project, test_version, False, test_fast_build)

        self.api_mock.start_build.assert_called_with(
            test_project, test_version, test_fast_build)

    def test_deploy_apk(self):
        self.mason.set_access_token("foo")
        self.mason.set_id_token("bar")

        self.mason.deploy('apk', 'TestItemName', '1.2.3.5.3.6', 'development', False, False)

        self.api_mock.deploy_artifact.assert_called_with(
            'apk', 'TestItemName', '1.2.3.5.3.6', 'development', False, False)


if __name__ == '__main__':
    unittest.main()
