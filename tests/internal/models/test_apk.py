import os
import unittest

import click
from mock import MagicMock

from cli.internal.models.apk import Apk
from tests import __tests_root__


class ApkTest(unittest.TestCase):
    def setUp(self):
        config = MagicMock()

        test_package_name = 'com.this.is.a.test'
        test_package_version = '11'
        test_package_version_code = 16

        apkf = MagicMock()
        apkf.package = MagicMock(return_value=test_package_name)
        apkf.get_androidversion_name = MagicMock(return_value=test_package_version)
        apkf.get_androidversion_code = MagicMock(return_value=test_package_version_code)
        apkf.is_valid_APK = MagicMock(return_value=True)
        apkf.get_min_sdk_version = MagicMock(return_value=23)

        self.test_apk = Apk(config, MagicMock(), apkf)

    def test_apk_is_valid(self):
        self.assertIsNone(self.test_apk.validate())

    def test_apk_content_type(self):
        self.assertEqual(
            self.test_apk.get_content_type(), 'application/vnd.android.package-archive')

    def test_apk_type(self):
        self.assertEqual(self.test_apk.get_type(), 'apk')

    def test_apk_pretty_type(self):
        self.assertEqual(self.test_apk.get_pretty_type(), 'App')

    def test_apk_sub_type(self):
        self.assertIsNone(self.test_apk.get_sub_type())

    def test_apk_name(self):
        self.assertEqual(self.test_apk.get_name(), self.test_apk.apk.get_package())

    def test_apk_version(self):
        self.assertEqual(self.test_apk.get_version(), self.test_apk.apk.get_androidversion_code())

    def test_apk_meta_data(self):
        meta_data = {
            'apk': {
                'versionName': self.test_apk.apk.get_androidversion_name(),
                'versionCode': self.test_apk.apk.get_androidversion_code(),
                'packageName': self.test_apk.apk.get_package()
            },
        }

        self.assertEqual(self.test_apk.get_registry_meta_data(), meta_data)

    def test_apk_v1_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, os.path.join(__tests_root__, 'res/v1.apk'))

        self.assertIsNotNone(apk)

    def test_apk_v2_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, os.path.join(__tests_root__, 'res/v2.apk'))

        self.assertIsNotNone(apk)

    def test_apk_v1_and_v2_signed(self):
        mock_config = MagicMock()
        apk = Apk.parse(mock_config, os.path.join(__tests_root__, 'res/v1and2.apk'))

        self.assertIsNotNone(apk)

    def test_apk_unsigned(self):
        mock_config = MagicMock()

        with self.assertRaises(click.Abort):
            Apk.parse(mock_config, os.path.join(__tests_root__, 'res/unsigned.apk'))

    def test_apk_debug_signed(self):
        mock_config = MagicMock()

        with self.assertRaises(click.Abort):
            Apk.parse(mock_config, os.path.join(__tests_root__, 'res/debug.apk'))
