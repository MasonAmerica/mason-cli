from mock import MagicMock
from mock import Mock


class Common(object):

    @staticmethod
    def create_mock_config():
        mock_config = Mock()
        return mock_config

    @staticmethod
    def create_mock_apk_file():
        test_package_name = 'com.this.is.a.test'
        test_package_version = '11'
        test_package_version_code = 16

        mock_apk = Mock()
        mock_apk.package = MagicMock(return_value=test_package_name)
        mock_apk.get_androidversion_name = MagicMock(return_value=test_package_version)
        mock_apk.get_androidversion_code = MagicMock(return_value=test_package_version_code)
        mock_apk.is_valid_APK = MagicMock(return_value=True)
        mock_apk.get_min_sdk_version = MagicMock(return_value=23)
        return mock_apk

    @staticmethod
    def create_mock_cert_finder():
        mock_finder = Mock()
        mock_finder.find = MagicMock(return_value='foo')
        return mock_finder

    @staticmethod
    def create_mock_media_file():
        test_bootanimation_name = 'test-boot'
        test_bootanimation_version = 1
        test_bootanimation_type = 'media'
        test_bootanimation_sub_type = 'bootanimation'
        test_bootanimation_content_type = 'application/zip'
        test_bootanimation_meta_data = {
            'media': {
                'type': test_bootanimation_sub_type,
            },
        }

        mock_media = Mock()
        mock_media.get_name = MagicMock(return_value=test_bootanimation_name)
        mock_media.get_version = MagicMock(return_value=test_bootanimation_version)
        mock_media.get_type = MagicMock(return_value=test_bootanimation_type)
        mock_media.get_sub_type = MagicMock(return_value=test_bootanimation_sub_type)
        mock_media.get_content_type = MagicMock(return_value=test_bootanimation_content_type)
        mock_media.get_registry_meta_data = MagicMock(return_value=test_bootanimation_meta_data)
        mock_media.validate = MagicMock()
        return mock_media

    @staticmethod
    def create_config_file():
        test_ecosystem_definition = {
            'os': {
                'name': 'test',
                'version': 1
            }
        }
        return test_ecosystem_definition
