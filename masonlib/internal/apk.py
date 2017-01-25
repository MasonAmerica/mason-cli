import os
import re

from masonlib.external.apk_parse.apk import APK
from masonlib.internal.artifacts import IArtifact


class Apk(IArtifact):

    def __init__(self, apkf):
        self.apkf = apkf
        self.name = self.apkf.package
        self.version = self.apkf.get_androidversion_code()
        self.details = self.apkf.cert_text

    @staticmethod
    def parse(config, apk):
        if not os.path.isfile(apk):
            print 'No file provided'
            return False

        apk_abs = APK(apk)
        apkf = Apk(apk_abs)

        # Bail on non valid apk
        if not apkf.is_valid():
            print "Not a valid APK, only APK's are currently supported"
            return False

        # Check for 'Android Debug' CN for the given artifact, disallow upload
        for line in apkf.details:
            if re.search('Subject:', line):
                if re.search('Android Debug', line):
                    print '\n------------------WARNING------------------\n' \
                          'Not allowing android debug key signed apk. \n' \
                          'Please sign the APK with your release keys \n' \
                          'before attempting to upload.               \n' \
                          '------------------WARNING------------------\n'
                    return False

        print '------------ APK ------------'
        print 'File Name: {}'.format(apk)
        print 'File size: {}'.format(os.path.getsize(apk))
        print 'Package: {}'.format(apkf.apkf.package)
        print 'Version Name: {}'.format(apkf.apkf.get_androidversion_name())
        print 'Version Code: {}'.format(apkf.apkf.get_androidversion_code())
        if config.verbose:
            for line in apkf.details:
                print line
        print '-----------------------------'
        return apkf

    def is_valid(self):
        try:
            value = int(self.version)
            if value > 2147483647:
                raise ValueError('The apk versionCode cannot be larger than MAX_INT (2147483647)')
        except ValueError as err:
            print "Error in configuration file: {}".format(err)
            return False
        return self.apkf.is_valid_APK()

    def get_content_type(self):
        return 'application/vnd.android.package-archive'

    def get_type(self):
        return 'apk'

    def get_sub_type(self):
        return None

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        meta_data = {
            'apk': {
                'versionName': self.apkf.get_androidversion_name(),
                'versionCode': self.apkf.get_androidversion_code(),
                'packageName': self.apkf.package
            },
        }
        return meta_data

    def get_details(self):
        return self.details