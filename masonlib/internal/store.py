import yaml
import os

CURRENT_CONFIG_VERSION = 1

class Store(object):
    CONFIG_VERSION = 'config_version'
    CLIENT_ID = 'client_id'
    AUTH_URL = 'auth_url'
    USER_INFO_URL = 'user_info_url'
    REGISTRY_SIGNED_URL = 'registry_signed_url'
    REGISTRY_ARTIFACT_URL = 'registry_artifact_url'
    BUILDER_URL = 'builder_url'
    DEPLOY_URL = 'deploy_url'

    def __init__(self, file_path):
        self.file = file_path
        self.data = self._load_stored_data()
        if not self._validate_data():
            print 'Resetting config...'
            os.remove(file_path)
            self.data = self._load_stored_data()

    def _load_stored_data(self):
        if not os.path.isfile(self.file):
            config = self._default_config()
            with open(self.file, 'w') as stream:
                stream.write(yaml.dump(config))
        else:
            with open(self.file, 'r') as stream:
                try:
                    config = yaml.load(stream, Loader=yaml.SafeLoader)
                except yaml.YAMLError as exc:
                    print(exc)
                    return
        return config

    def _validate_data(self):
        return self.CLIENT_ID in self.data and \
               self.AUTH_URL in self.data and \
               self.USER_INFO_URL in self.data and \
               self.REGISTRY_SIGNED_URL in self.data and \
               self.REGISTRY_ARTIFACT_URL in self.data and \
               self.BUILDER_URL in self.data and \
               self.DEPLOY_URL in self.data and \
               self.CONFIG_VERSION in self.data and self.data[self.CONFIG_VERSION] == CURRENT_CONFIG_VERSION

    def _default_config(self):
        return {
            self.CLIENT_ID: 'QLWpUwYOOcLlAJsmyQhQMXyeWn6RZpoc',
            self.AUTH_URL: 'https://bymason.auth0.com/oauth/ro',
            self.USER_INFO_URL: 'https://bymason.auth0.com/userinfo',
            self.REGISTRY_ARTIFACT_URL: 'https://platform.bymason.com/api/registry/artifacts',
            self.REGISTRY_SIGNED_URL: 'https://platform.bymason.com/api/registry/signedurl',
            self.BUILDER_URL: 'https://platform.bymason.com/api/tracker/builder',
            self.DEPLOY_URL: 'https://platform.bymason.com/api/deploy',
            self.CONFIG_VERSION: CURRENT_CONFIG_VERSION
        }

    def _get(self, key):
        if not self.data or key not in self.data:
            return None
        else:
            return self.data[key]

    def reload(self):
        self.data = self._load_stored_data()

    def client_id(self):
        return self._get(self.CLIENT_ID)

    def auth_url(self):
        return self._get(self.AUTH_URL)

    def user_info_url(self):
        return self._get(self.USER_INFO_URL)

    def registry_signer_url(self):
        return self._get(self.REGISTRY_SIGNED_URL)

    def registry_artifact_url(self):
        return self._get(self.REGISTRY_ARTIFACT_URL)

    def builder_url(self):
        return self._get(self.BUILDER_URL)

    def deploy_url(self):
        return self._get(self.DEPLOY_URL)
