# COPYRIGHT MASONAMERICA
import unittest

from masonlib.imason import IMason
from masonlib.internal.apk import Apk
from masonlib.platform import Platform
from test_common import Common


class MasonTest(unittest.TestCase):

    def setUp(self):
        config = Common.create_mock_config()
        platform = Platform(config)
        self.mason = platform.get(IMason)

    def test_authenticate(self):
        test_user = 'foo'
        test_password = 'bar'

        store = Common.create_mock_store()
        self.mason.set_id_token('09ads09a8dsfa0re')
        self.mason.set_access_token('oads098fa9830924qdf09asfd')
        self.mason.store = store

        expected_payload = {'client_id': store.client_id(),
                   'username': test_user,
                   'password': test_password,
                   'id_token': '09ads09a8dsfa0re',
                   'connection': 'Username-Password-Authentication',
                   'grant_type': 'password',
                   'scope': 'openid',
                   'device': ''}

        assert(expected_payload == self.mason._get_auth_payload(test_user, test_password))

    def test__request_signed_url(self):
        apkf = Common.create_mock_apk_file()
        store = Common.create_mock_store()

        test_md5 = 'l32k43h2lh532k32jkfods9ads348aisdfiuaoer034f7s9347u123'
        test_customer = 'mason'
        test_apk = Apk(apkf)

        self.mason.set_id_token('09ads09a8dsfa0re')
        self.mason.set_access_token('oads098fa9830924qdf09asfd')
        self.mason.store = store

        expected_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 09ads09a8dsfa0re',
                            'Content-MD5': u'bDMyazQzaDJsaDUzMmszMmprZm9kczlhZHMzNDhhaXNkZml1YW9lcjAzNGY3czkzNDd1MTIz'}

        # test getting the signed url request headers
        assert(expected_headers == self.mason._get_signed_url_request_headers(test_md5))
        expected_url = store.registry_signer_url() \
              + '/{0}/{1}/{2}'.format(test_customer, test_apk.get_name(), test_apk.get_version()) \
              + '?type=' + test_apk.get_type()
        # test getting the signed url endpoint
        actual_url = self.mason._get_signed_url_request_endpoint(test_customer, test_apk)
        assert(expected_url == actual_url)

    def test__upload_to_signed_url(self):
        apkf = Common.create_mock_apk_file()
        store = Common.create_mock_store()

        test_md5 = 'l32k43h2lh532k32jkfods9ads348aisdfiuaoer034f7s9347u123'
        test_apk = Apk(apkf)

        self.mason.set_id_token('09ads09a8dsfa0re')
        self.mason.set_access_token('oads098fa9830924qdf09asfd')
        self.mason.store = store

        expected_headers = {'Content-Type': test_apk.get_content_type(),
         'Content-MD5': u'bDMyazQzaDJsaDUzMmszMmprZm9kczlhZHMzNDhhaXNkZml1YW9lcjAzNGY3czkzNDd1MTIz'}

        assert(expected_headers == self.mason._get_signed_url_post_headers(test_apk, test_md5))

    def test__register_to_mason(self):
        apkf = Common.create_mock_apk_file()
        store = Common.create_mock_store()

        test_download_url = 'https://signed.magic.url.in.the.sky'
        test_sha1 = 'l32k43h2lh532k32jkfods9ads348aisdfiuaoer034f7s9347u123'
        test_customer = 'mason'
        test_apk = Apk(apkf)

        self.mason.set_id_token('09ads09a8dsfa0re')
        self.mason.set_access_token('oads098fa9830924qdf09asfd')
        self.mason.store = store

        expected_payload = {'name': test_apk.get_name(),
                            'version': test_apk.get_version(),
                            'customer': test_customer,
                            'url': test_download_url,
                            'type': test_apk.get_type(),
                            'checksum': {
                                'sha1': test_sha1
                            }}

        assert(expected_payload == self.mason._get_registry_payload(test_customer, test_download_url, test_sha1,
                                                                    test_apk))

        expected_updated_payload = {'name': test_apk.get_name(),
                                    'version': test_apk.get_version(),
                                    'customer': test_customer,
                                    'url': test_download_url,
                                    'type': test_apk.get_type(),
                                    'checksum': {
                                        'sha1': test_sha1
                                    },
                                    'apk': {
                                        'versionName': test_apk.apkf.get_androidversion_name(),
                                        'versionCode': test_apk.apkf.get_androidversion_code(),
                                        'packageName': test_apk.apkf.package
                                    },
                                    }

        expected_payload.update(test_apk.get_registry_meta_data())

        assert(expected_updated_payload == expected_payload)

    def test__build_project(self):
        test_customer = 'mason-test'
        test_project = 'TestProjectName'
        test_version = '1.3.2.5.2.13.6'

        expected_payload = {'customer': test_customer,
                'project': test_project,
                'version': test_version}

        assert(expected_payload == self.mason._get_build_payload(test_customer, test_project, test_version))

    def test__deploy_item(self):
        test_customer = 'mason-test'
        test_item = 'TestItemName'
        test_version = '1.2.3.5.3.6'
        test_group = 'development'
        test_item_type = 'apk'
        test_push = False

        expected_payload = {
            'customer': test_customer,
            'group': test_group,
            'name': test_item,
            'version': test_version,
            'type': test_item_type,
            'push': test_push
        }

        assert(expected_payload ==
               self.mason._get_deploy_payload(test_customer, test_group, test_item, test_version, test_item_type,
                                              test_push))

if __name__ == '__main__':
    unittest.main()
