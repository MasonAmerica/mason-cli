import unittest

from masonlib.internal.apk import Apk
from test_common import Common


class ApkTest(unittest.TestCase):

    def setUp(self):
        self.test_apk = self._create_test_apk()

    def test_apk_is_valid(self):
        assert(self.test_apk.is_valid())

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

    @staticmethod
    def _create_test_apk():
        apkf = Common.create_mock_apk_file()
        return Apk(apkf)
