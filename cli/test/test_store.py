import os
import unittest

import yaml

from cli.internal.utils.store import Store


class StoreTest(unittest.TestCase):
    CLIENT_ID = 'APODf8uaspoerpsd8fuyadoreafds89u7fDDS8f'
    AUTH_URL = 'http://auth.server.in.the.sky'
    USER_INFO_URL = 'http://user.info.server.in.the.sky'
    REGISTRY_SIGNED_URL = 'http://registry.signed.url.in.the.sky'
    REGISTRY_ARTIFACT_URL = 'http://artifact.signed.url.in.the.sky'
    BUILDER_URL = 'https://builder.url.in.the.sky'
    DEPLOY_URL = 'https://deploy.url.in.the.sky'

    def setUp(self):
        self.store = Store('test', {})
        self._write_test_credentials()
        self.store.restore()

    def tearDown(self):
        os.remove(self.store.file)

    def _write_test_credentials(self):
        test_data = {
            'client_id': self.CLIENT_ID,
            'auth_url': self.AUTH_URL,
            'user_info_url': self.USER_INFO_URL,
            'registry_signed_url': self.REGISTRY_SIGNED_URL,
            'registry_artifact_url': self.REGISTRY_ARTIFACT_URL,
            'builder_url': self.BUILDER_URL,
            'deploy_url': self.DEPLOY_URL
        }

        if not os.path.exists(os.path.dirname(self.store.file)):
            os.makedirs(os.path.dirname(self.store.file))
        with open(self.store.file, 'w') as outfile:
            yaml.dump(test_data, outfile)

    def test_client_id(self):
        assert (self.CLIENT_ID == self.store['client_id'])

    def test_auth_url(self):
        assert (self.AUTH_URL == self.store['auth_url'])

    def test_user_info_url(self):
        assert (self.USER_INFO_URL == self.store['user_info_url'])

    def test_registry_signer_url(self):
        assert (self.REGISTRY_SIGNED_URL == self.store['registry_signed_url'])

    def test_registry_artifact_url(self):
        assert (self.REGISTRY_ARTIFACT_URL == self.store['registry_artifact_url'])

    def test_builder_url(self):
        assert (self.BUILDER_URL == self.store['builder_url'])

    def test_deploy_url(self):
        assert (self.DEPLOY_URL == self.store['deploy_url'])
