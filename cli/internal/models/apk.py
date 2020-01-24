import inspect
import logging
import os
import re
from subprocess import PIPE
from subprocess import Popen

import click
from pyaxmlparser import APK

from cli.internal.models.artifacts import IArtifact
from cli.internal.utils.validation import validate_artifact_version

# Disable pyaxmlparser logs since it spits out unnecessary warnings
logging.getLogger("pyaxmlparser.core").setLevel("ERROR")


class Apk(IArtifact):
    def __init__(self, config, binary, apkf, cert_finder=None):
        self.config = config
        self.binary = binary
        self.apkf = apkf
        self.cert_finder = cert_finder or CertFinder(apkf)
        self.name = self.apkf.package
        self.version = self.apkf.get_androidversion_code()
        self.details = None

    @staticmethod
    def parse(config, apk):
        apk_abs = APK(apk)

        apkf = Apk(config, apk, apk_abs)
        apkf.validate()
        return apkf

    # TODO: Move this entire validation to service side.
    def validate(self):
        validate_artifact_version(self.config, self.version, self.get_type())

        # If not parsed well by apk_parse
        if not self.apkf.is_valid_APK():
            self.config.logger.error('Not a valid APK.')
            raise click.Abort()

        # We don't support anything higher right now
        if int(self.apkf.get_min_sdk_version()) > 25:
            self.config.logger.error(inspect.cleandoc("""
                File Name: {}

                Mason Platform does not currently support applications with a minimum sdk greater
                than API 25. Please lower the minimum sdk value in your manifest or
                gradle file.
            """.format(self.apkf.filename)))
            raise click.Abort()

        # Check if the app was signed with v1
        if not self.get_details():
            self.config.logger.error(inspect.cleandoc("""
                File Name: {}

                A v1 signing certificate was not detected.
                Mason Platform requires your app to be signed with a v1 signing scheme. Please
                ensure your app is either signed exclusively with v1 or with some combination
                of v1 and other signing schemes. For more details on app signing, visit
                https://s.android.com/security/apksigning
            """.format(self.apkf.filename)))
            raise click.Abort()

        # Check for 'Android Debug' CN for the given artifact, disallow upload
        for line in self.get_details().split('\n'):
            if re.search('Subject:', line) or re.search('Owner:', line):
                if re.search('Android Debug', line):
                    self.config.logger.error(inspect.cleandoc("""
                        Apps signed with a debug key are not allowed.
                        Please sign the APK with your release keys and try again.
                    """))
                    raise click.Abort()

    def log_details(self):
        self.config.logger.info('------------ APK ------------')
        self.config.logger.info('File Name: {}'.format(self.binary))
        self.config.logger.info('File size: {}'.format(os.path.getsize(self.binary)))
        self.config.logger.info('Package: {}'.format(self.apkf.package))
        self.config.logger.info('Version Name: {}'.format(self.apkf.get_androidversion_name()))
        self.config.logger.info('Version Code: {}'.format(self.apkf.get_androidversion_code()))
        self.config.logger.debug(self.get_details())
        self.config.logger.info('-----------------------------')

    def get_content_type(self):
        return 'application/vnd.android.package-archive'

    def get_type(self):
        return 'apk'

    def get_sub_type(self):
        return

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

    def __eq__(self, other):
        return self.binary == other.binary


class CertFinder:
    def __init__(self, apkf):
        self.apkf = apkf

    def find(self):
        cert = None
        for file in self.apkf.files:
            # Cert files are NOT necessarily named 'CERT.RSA'
            if file.endswith('.RSA'):
                cert = self.apkf.get_file(file)
                break
        if not cert:
            return

        try:
            p = Popen(['openssl', 'pkcs7', '-inform', 'DER', '-noout', '-print_certs', '-text'],
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
        except OSError or FileNotFoundError:
            root = os.path.dirname(os.path.realpath(__file__))
            openssl = os.path.join(root, "openssl.exe")
            p = Popen([openssl, 'pkcs7', '-inform', 'DER', '-noout', '-print_certs', '-text'],
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
        return p.communicate(input=cert)[0].decode('utf-8')
