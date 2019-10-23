import os
import re

from pyaxmlparser import APK
from pyaxmlparser.core import FileNotPresent
from masonlib.internal.artifacts import IArtifact
from subprocess import Popen, PIPE


class Apk(IArtifact):
    def __init__(self, apkf, cert_finder=None):
        self.apkf = apkf
        self.cert_finder = cert_finder or CertFinder(apkf)
        self.name = self.apkf.package
        self.version = self.apkf.get_androidversion_code()
        self.details = None

    @staticmethod
    def parse(config, apk):
        if not os.path.isfile(apk):
            print('No file provided')
            return None

        apk_abs = APK(apk)
        apkf = Apk(apk_abs)

        # Bail on non valid apk
        if not apkf or not apkf.is_valid():
            return None

        # Check for 'Android Debug' CN for the given artifact, disallow upload
        for line in apkf.get_details().split('\n'):
            if re.search('Subject:', line) or re.search('Owner:', line):
                if re.search('Android Debug', line):
                    print('\n----------- ERROR -----------\n' \
                          'Not allowing android debug key signed apk. \n' \
                          'Please sign the APK with your release keys \n' \
                          'before attempting to upload.               \n' \
                          '-----------------------------\n')
                    return None
            elif re.search('Not a signed jar file', line):
                print('\n----------- ERROR -----------\n' \
                    'No certificate was detected in your APK. \n' \
                    'Please sign the APK with your release keys \n' \
                    'before attempting to upload.               \n' \
                    '-----------------------------\n')
                return None

        print('------------ APK ------------')
        print('File Name: {}'.format(apk))
        print('File size: {}'.format(os.path.getsize(apk)))
        print('Package: {}'.format(apkf.apkf.package))
        print('Version Name: {}'.format(apkf.apkf.get_androidversion_name()))
        print('Version Code: {}'.format(apkf.apkf.get_androidversion_code()))
        if config.verbose:
            for line in apkf.get_details():
                print(line)
        print('-----------------------------')
        return apkf

    def is_valid(self):
        try:
            value = int(self.version)
            if value > 2147483647:
                raise ValueError('The apk versionCode cannot be larger than MAX_INT (2147483647)')
        except ValueError as err:
            print("Error in configuration file: {}".format(err))
            return False

        # TODO: Move this entire validation to service side.
        # if not parsed well by apk_parse
        if not self.apkf.is_valid_APK():
            print("Not a valid APK, only APK's are currently supported")
            return False

        # We don't support anything higher than Marshmallow as a min right now
        if int(self.apkf.get_min_sdk_version()) > 23:
            print('\n----------- ERROR -----------\n' \
                  "File Name: {}\n" \
                  "Details:\n" \
                  "  Mason Platform does not currently support applications with a minimum sdk\n" \
                  "  greater than 23 (Marshmallow). Please lower the minimum sdk value in your\n" \
                  "  manifest or gradle file.\n" \
                   '-----------------------------\n'.format(self.apkf.filename))
            return False

        # We can safely assume since this cert wasn't provided that we're dealing with a v2 signed apk.
        if not self.get_details():
            print('\n----------- ERROR -----------\n' \
                  "File Name: {}\n" \
                  "Details:\n" \
                  "  Mason Platform does not currently support v2 signing scheme for APK's.\n" \
                  "  Full Apk (v2) signing is included for Nougat devices and an option in \n" \
                  "  Android Studio 2.3+. Please select to either sign the APK with both v1 \n" \
                  "  (Jar Signature) and v2 (Full APK Signature) or v1 alone. For further\n" \
                  "  details reference https://source.android.com/security/apksigning/index.html#\n" \
                  '-----------------------------\n'.format(self.apkf.filename))
            return False

        return True

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
        if not self.details:
            self.details = self.cert_finder.find()
        return self.details


class CertFinder:
    def __init__(self, apkf):
        self.apkf = apkf

    def find(self):
        try:
            cert = self.apkf.get_file("META-INF/CERT.RSA")
            p = Popen(['openssl', 'pkcs7', '-inform', 'DER', '-noout', '-print_certs', '-text'],
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
            return p.communicate(input=cert)[0].decode('utf-8')
        except FileNotPresent:
            return None
