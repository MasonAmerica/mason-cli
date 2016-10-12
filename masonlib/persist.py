# COPYRIGHT MASONAMERICA
import json
import os

from os.path import expanduser

class Persist(object):

    def __init__(self, file_path):
        home = expanduser("~")
        self.file = os.path.join(home, file_path)
        self.data = self.__load_stored_data()

    def __load_stored_data(self):
        if not os.path.isfile(self.file):
            return None

        with open(self.file) as data_file:
            try:
                data = json.load(data_file)
                return data
            except ValueError:
                return None

    def __get(self, key):
        if not self.data or key not in self.data:
            return None
        else:
            return self.data[key]

    def reload(self):
        self.data = self.__load_stored_data()

    def retrieve_id_token(self):
        return self.__get('id_token')

    def retrieve_access_token(self):
        return self.__get('access_token')

    def write_tokens(self, data):
        with open(self.file, 'w') as outfile:
            json.dump(data, outfile)
            return True