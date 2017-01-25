import unittest

from test_common import Common


class MediaTest(unittest.TestCase):

    def setUp(self):
        self.media = self._create_media()

    def test_media_is_valid(self):
        assert(self.media.is_valid())

    def test_media_content_type(self):
        if self.media.get_sub_type() == 'bootanimation':
            assert(self.media.get_content_type() == 'application/zip')
        else:
            raise AssertionError('Unknown subtype')

    def test_media_type(self):
        assert(self.media.get_type() == 'media')

    def test_media_sub_type(self):
        assert(self.media.get_sub_type() is not None)

    def test_media_name(self):
        assert(self.media.get_name() == 'test-boot')

    def test_media_version(self):
        assert(self.media.get_version() == 1.0)

    def test_media_meta_data(self):
        meta_data = {
            'media': {
                'type': self.media.get_sub_type(),
            },
        }
        assert(self.media.get_registry_meta_data() == meta_data)

    @staticmethod
    def _create_media():
        media = Common.create_mock_media_file()
        return media
