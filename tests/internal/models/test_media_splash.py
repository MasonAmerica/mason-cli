import os
import unittest

from mock import MagicMock

from cli.internal.models.media import Media
from tests import __tests_root__


class MediaSplashTest(unittest.TestCase):
    def setUp(self):
        media_file = os.path.join(__tests_root__, 'res', 'splash.png')
        self.media = Media(MagicMock(), 'test-splash', 'splash', 1, media_file)

    def test_media_is_valid(self):
        self.assertIsNone(self.media.validate())

    def test_media_content_type(self):
        self.assertEqual(self.media.get_content_type(), 'image/png')

    def test_media_type(self):
        self.assertEqual(self.media.get_type(), 'media')

    def test_media_sub_type(self):
        self.assertEqual(self.media.get_sub_type(), 'splash')

    def test_media_name(self):
        self.assertEqual(self.media.get_name(), 'test-splash')

    def test_media_version(self):
        self.assertEqual(self.media.get_version(), '1')

    def test_media_meta_data(self):
        meta_data = {
            'media': {
                'type': self.media.get_sub_type(),
            },
        }

        self.assertEqual(self.media.get_registry_meta_data(), meta_data)
