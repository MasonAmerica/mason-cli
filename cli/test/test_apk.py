import unittest

import click
from mock import MagicMock
from test_common import Common

from cli.internal.apk import Apk


class ApkTest(unittest.TestCase):

    def setUp(self):
        self.test_apk = self._create_test_apk()

    def test_apk_is_valid(self):
        self.test_apk.validate()

    def test_apk_content_type(self):
        assert(self.test_apk.get_content_type() == 'application/vnd.android.package-archive')

    def test_apk_type(self):
        assert(self.test_apk.get_type() == 'apk')

    def test_apk_sub_type(self):
        assert(self.test_apk.get_sub_type() is None)

    def test_apk_name(self):
        assert(self.test_apk.get_name() == self.test_apk.apkf.package)

    def test_apk_version(self):
        assert(self.test_apk.get_version() == self.test_apk.apkf.get_androidversion_code())

    def test_apk_meta_data(self):
        meta_data = {
            'apk': {
                'versionName': self.test_apk.apkf.get_androidversion_name(),
                'versionCode': self.test_apk.apkf.get_androidversion_code(),
                'packageName': self.test_apk.apkf.package
            },
        }
        assert(self.test_apk.get_registry_meta_data() == meta_data)

    def test_apk_v1_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, "res/v1.apk")
        self.assertIsNotNone(apk)
        apk.validate()

    @unittest.skip("V2-only signing is not yet supported")
    def test_apk_v2_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, "res/v2.apk")
        self.assertIsNotNone(apk)
        self.assertTrue(apk.validate(), "APK is invalid!")

    def test_apk_v1_and_v2_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, "res/v1and2.apk")
        self.assertIsNotNone(apk)
        apk.validate()

    def test_apk_unsigned(self):
        mock_config = MagicMock()
        self.assertRaises(click.Abort, Apk.parse, mock_config, "res/unsigned.apk")

    def test_apk_debug_signed(self):
        mock_config = MagicMock()
        self.assertRaises(click.Abort, Apk.parse, mock_config, "res/debug.apk")

    @staticmethod
    def _create_test_apk():
        config = Common.create_mock_config()
        apkf = Common.create_mock_apk_file()
        cert_finder = Common.create_mock_cert_finder()
        return Apk(config, apkf, cert_finder)
