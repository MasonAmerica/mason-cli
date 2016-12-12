import yaml
import os

class Store(object):

    def __init__(self, file_path):
        self.file = file_path
        self.data = self.__load_stored_data()
        if not self.__validate_data():
            print 'Resetting credential store...'
            os.remove(file_path)
            self.data = self.__load_stored_data()

    def __load_stored_data(self):
        if not os.path.isfile(self.file):
            config = self._default_config()
            with open(self.file, 'w') as stream:
                stream.write(yaml.dump(config))
        else:
            with open(self.file, 'r') as stream:
                try:
                    config = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
        return config

    def __validate_data(self):
        return 'client_id' in self.data and \
               'auth_url' in self.data and \
               'user_info_url' in self.data and \
               'registry_artifact_url' in self.data and \
               'registry_signed_url' in self.data

    def _default_config(self):
        return {
            'client_id': 'QLWpUwYOOcLlAJsmyQhQMXyeWn6RZpoc',
            'auth_url': 'https://bymason.auth0.com/oauth/ro',
            'user_info_url': 'https://bymason.auth0.com/userinfo',
            'registry_artifact_url': 'https://platform.bymason.com/api/registry/artifacts',
            'registry_signed_url': 'https://platform.bymason.com/api/registry/signedurl',
        }

    def __get(self, key):
        if not self.data or key not in self.data:
            return None
        else:
            return self.data[key]

    def reload(self):
        self.data = self.__load_stored_data()

    def client_id(self):
        return self.__get('client_id')

    def auth_url(self):
        return self.__get('auth_url')

    def user_info_url(self):
        return self.__get('user_info_url')

    def registry_signer_url(self):
        return self.__get('registry_signed_url')

    def registry_artifact_url(self):
        return self.__get('registry_artifact_url')
