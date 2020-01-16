# COPYRIGHT MASONAMERICA
import unittest

from mock import MagicMock
from test_common import Common

from cli.internal.masoncli import MasonCli
from cli.internal.utils.constants import ENDPOINTS


class MasonTest(unittest.TestCase):

    def setUp(self):
        config = Common.create_mock_config()
        api_mock = MagicMock()
        cli = MasonCli(config)
        cli.api = api_mock

        self.mason = cli
        self.api_mock = api_mock

    def test_authenticate(self):
        test_user = 'foo'
        test_password = 'bar'

        self.mason.set_id_token('09ads09a8dsfa0re')
        self.mason.set_access_token('oads098fa9830924qdf09asfd')

        expected_payload = {
            'client_id': ENDPOINTS['client_id'],
            'username': test_user,
            'password': test_password,
            'id_token': '09ads09a8dsfa0re',
            'connection': 'Username-Password-Authentication',
            'grant_type': 'password',
            'scope': 'openid',
            'device': ''
        }

        assert (expected_payload == self.mason._get_auth_payload(test_user, test_password))

    def test_register_apk(self):
        apkf = "res/v1.apk"
        self.mason.register_apk(apkf)

        self.api_mock.upload_artifact.assert_called_with(apkf, self.mason.artifact)

    def test__build_project(self):
        test_customer = 'mason-test'
        test_project = 'TestProjectName'
        test_version = '1.3.2.5.2.13.6'
        test_fast_build = False

        expected_payload = {'customer': test_customer,
                            'project': test_project,
                            'version': test_version}

        assert (expected_payload == self.mason._get_build_payload(test_customer, test_project,
                                                                  test_version, test_fast_build))

    def test__build_project_fast_build(self):
        test_customer = 'mason-test'
        test_project = 'TestProjectName'
        test_version = '1.3.2.5.2.13.6'
        test_fast_build = True

        expected_payload = {'customer': test_customer,
                            'project': test_project,
                            'version': test_version,
                            'fastBuild': test_fast_build}

        assert (expected_payload == self.mason._get_build_payload(test_customer, test_project,
                                                                  test_version, test_fast_build))

    def test_deploy_apk(self):
        self.mason.deploy('apk', 'TestItemName', '1.2.3.5.3.6', 'development', False, False)

        self.api_mock.deploy_artifact.assert_called_with(
            'apk', 'TestItemName', '1.2.3.5.3.6', 'development', False, False)


if __name__ == '__main__':
    unittest.main()
