from artifacts import Artifact

import os
import yaml

class OSConfig(Artifact):

    def __init__(self, ecosystem):
        self.ecosystem = ecosystem
        self.os = self.ecosystem['os']
        self.name = self.os['name']
        self.version = self.os['version']

    @staticmethod
    def parse(config, config_yaml):
        if not os.path.isfile(config_yaml):
            print 'No file provided'
            return None

        ecosystem = OSConfig.__load_ecosystem(config_yaml)
        os_config = OSConfig(ecosystem)

        # Bail on non valid apk
        if not os_config.is_valid():
            print "Not a valid os configuration"
            return None

        print '--------- OS Config ---------'
        print 'File Name: ' + config_yaml
        print 'File size: ' + str(os.path.getsize(config_yaml))
        print 'Name: ' + os_config.name
        print 'Version: ' + os_config.version
        if config.verbose:
            for k, v in os_config.ecosystem.iteritems():
                print k, v
        print '-----------------------------'
        return os_config

    def is_valid(self):
        if not self.ecosystem or not self.os or not self.name or not self.version:
            return False
        return True

    def get_content_type(self):
        return 'text/x-yaml'

    def get_type(self):
        return 'config'

    def get_sub_type(self):
        return None

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        return None

    def get_details(self):
        return self.ecosystem

    @staticmethod
    def __load_ecosystem(path):
        if not os.path.isfile(path):
            return None

        with open(path) as data_file:
            try:
                data = yaml.load(data_file)
                return data
            except ValueError:
                return None