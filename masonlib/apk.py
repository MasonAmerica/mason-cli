from artifacts import Artifact

from lib.apk_parse.apk import APK

import re
import os

class Apk(Artifact):
    def __init__(self, apk):
        self.apkf = APK(apk)
        self.name = self.apkf.package
        self.version = self.apkf.get_androidversion_name()
        self.details = self.apkf.cert_text

    @staticmethod
    def parse(config, apk):
        if not os.path.isfile(apk):
            print 'No file provided'
            return False

        apkf = Apk(apk)

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
        print 'File Name: ' + apk
        print 'File size: ', str(os.path.getsize(apk))
        print 'Package: ' + apkf.apkf.package
        print 'Version Name: ' + apkf.apkf.get_androidversion_name()
        print 'Version Code: ' + apkf.apkf.get_androidversion_code()
        if config.verbose:
            for line in apkf.details:
                print line
        print '-----------------------------'
        return apkf

    def is_valid(self):
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
                'versionCode': self.apkf.get_androidversion_code(),
                'packageName': self.apkf.package
            },
        }
        return meta_data

    def get_details(self):
        return self.details