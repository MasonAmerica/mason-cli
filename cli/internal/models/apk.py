import inspect
import os

import click

from cli.config import Config
from cli.internal.models.apkparsing.apk import APK
from cli.internal.models.artifacts import IArtifact
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.logging import LazyLog
from cli.internal.utils.ui import section
from cli.internal.utils.validation import validate_artifact_version


class Apk(IArtifact):
    def __init__(self, config: Config, binary, apk: APK):
        self.config = config
        self.binary = binary
        self.apk = apk
        self.name = apk.get_package() if apk.is_valid_APK() else None
        self.version = apk.get_androidversion_code() if apk.is_valid_APK() else None
        self.details = None

    @staticmethod
    def parse(config, apk):
        parsed = Apk(config, apk, APK(apk))
        parsed.validate()
        return parsed

    # TODO: Move this entire validation to service side.
    def validate(self):
        # If not parsed well by apk_parse
        if not self.apk.is_valid_APK():
            self.config.logger.error('Not a valid APK.')
            raise click.Abort()

        validate_artifact_version(self.config, self.version, self.get_type())

        min_sdk = int(self.apk.get_min_sdk_version())
        # We don't support anything higher right now
        if min_sdk > 30:
            self.config.logger.error(inspect.cleandoc("""
                File Name: {}

                Mason Platform does not currently support applications with a minimum sdk greater
                than API 30. Please lower the minimum sdk value in your manifest or
                gradle file.
            """.format(self.binary)))
            raise click.Abort()

        is_debug = False
        if self.apk.is_signed_v1():
            for cert_name in self.apk.get_signature_names():
                cert = self.apk.get_certificate(cert_name)
                is_debug = is_debug or cert.subject.native.get('common_name', '') == 'Android Debug'
        elif min_sdk >= 25 and self.apk.is_signed_v2():
            for cert in self.apk.get_certificates_v2():
                is_debug = is_debug or cert.subject.native.get('common_name', '') == 'Android Debug'
        elif min_sdk >= 28 and self.apk.is_signed_v3():
            for cert in self.apk.get_certificates_v3():
                is_debug = is_debug or cert.subject.native.get('common_name', '') == 'Android Debug'
        else:
            self.config.logger.error(inspect.cleandoc("""
                File Name: {}

                A signing certificate was not detected.
                The Mason Platform requires your app to be signed with a signing scheme.
                For more details on app signing, visit https://s.android.com/security/apksigning.
            """.format(self.binary)))
            raise click.Abort()

        if is_debug:
            self.config.logger.error(inspect.cleandoc("""
                Apps signed with debug keys are not allowed.
                Please sign the APK with your release keys and try again.
            """))
            raise click.Abort()

    def log_details(self):
        with section(self.config, self.get_pretty_type()):
            self.config.logger.info('File path: {}'.format(self.binary))
            self.config.logger.info('Package name: {}'.format(self.get_name()))
            self.config.logger.info('Version name: {}'.format(self.apk.get_androidversion_name()))
            self.config.logger.info('Version code: {}'.format(self.apk.get_androidversion_code()))

            self.config.logger.debug(LazyLog(
                lambda: 'File size: {}'.format(os.path.getsize(self.binary))))
            self.config.logger.debug(LazyLog(
                lambda: 'File SHA256: {}'.format(hash_file(self.binary, 'sha256'))))
            self.config.logger.debug(LazyLog(
                lambda: 'File SHA1: {}'.format(hash_file(self.binary, 'sha1'))))
            self.config.logger.debug(LazyLog(
                lambda: 'File MD5: {}'.format(hash_file(self.binary, 'md5'))))

    def get_content_type(self):
        return 'application/vnd.android.package-archive'

    def get_type(self):
        return 'apk'

    def get_pretty_type(self):
        return 'App'

    def get_sub_type(self):
        return

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_registry_meta_data(self):
        meta_data = {
            'apk': {
                'versionName': self.apk.get_androidversion_name(),
                'versionCode': self.apk.get_androidversion_code(),
                'packageName': self.get_name()
            },
        }
        return meta_data

    def __eq__(self, other):
        return self.binary == other.binary
