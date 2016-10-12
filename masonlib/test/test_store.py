# COPYRIGHT MASONAMERICA
import unittest
import yaml
import os

from masonlib.store import Store

class StoreTest(unittest.TestCase):
    CLIENT_ID = 'APODf8uaspoerpsd8fuyadoreafds89u7fDDS8f'
    AUTH_URL = 'http://auth.server.in.the.sky'
    USER_INFO_URL = 'http://user.info.server.in.the.sky'
    REGISTRY_SIGNED_URL = 'http://registry.signed.url.in.the.sky'
    REGISTRY_ARTIFACT_URL = 'http://artifact.signed.url.in.the.sky'

    def setUp(self):
        self.store = Store('masonlib/.test_mason.yml')
        self.__write_test_credentials()
        self.store.reload()

    def tearDown(self):
        os.remove(self.store.file)

    def __write_test_credentials(self):
        test_data = {'client_id': self.CLIENT_ID,
                     'auth_url': self.AUTH_URL,
                     'user_info_url': self.USER_INFO_URL,
                     'registry_signed_url': self.REGISTRY_SIGNED_URL,
                     'registry_artifact_url': self.REGISTRY_ARTIFACT_URL}

        with open(self.store.file, 'w') as outfile:
            yaml.dump(test_data, outfile)

    def test_client_id(self):
        assert(self.CLIENT_ID == self.store.client_id())

    def test_auth_url(self):
        assert(self.AUTH_URL == self.store.auth_url())

    def test_user_info_url(self):
        assert(self.USER_INFO_URL == self.store.user_info_url())

    def test_registry_signer_url(self):
        assert(self.REGISTRY_SIGNED_URL == self.store.registry_signer_url())

    def test_registry_artifact_url(self):
        assert(self.REGISTRY_ARTIFACT_URL == self.store.registry_artifact_url())