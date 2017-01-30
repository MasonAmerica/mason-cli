from mock import MagicMock
from mock import Mock


class Common(object):

    @staticmethod
    def create_mock_config():
        mock_config = Mock()
        mock_config._check_version = MagicMock(return_value=None)
        mock_config.verbose = False

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
        return mock_apk

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
        mock_media.is_valid = MagicMock(return_value=True)
        return mock_media

    @staticmethod
    def create_config_file():
        test_ecosystem_definition = {
            'os': {
                'name' : 'test',
                'version' : 1
            }
        }
        return test_ecosystem_definition

    @staticmethod
    def create_mock_store():
        mock_store = Mock()
        mock_store.client_id = MagicMock(return_value='S(DF*SD($#hjLKA')
        mock_store.auth_url = MagicMock(return_value='https://secure.security.sec')
        mock_store.user_info_url = MagicMock(return_value='https://user.security.sec')
        mock_store.registry_signer_url = MagicMock(return_value='https://sign.security.sec')
        mock_store.registry_artifact_url = MagicMock(return_value='https://register.security.sec')
        return mock_store
