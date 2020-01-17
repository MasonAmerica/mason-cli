import unittest

import click
from mock import MagicMock

from cli.internal.utils.validation import validate_api_key
from cli.internal.utils.validation import validate_credentials
from cli.internal.utils.validation import validate_version


class ValidationTest(unittest.TestCase):
    def test__validate_credentials__no_tokens_fails(self):
        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(return_value=None)

        with self.assertRaises(click.Abort):
            validate_credentials(config)

    def test__validate_credentials__only_id_token_fails(self):
        def store(key):
            if key == 'id_token':
                return 'foo'

        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(side_effect=store)

        with self.assertRaises(click.Abort):
            validate_credentials(config)

    def test__validate_credentials__only_access_token_fails(self):
        def store(key):
            if key == 'access_token':
                return 'foo'

        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(side_effect=store)

        with self.assertRaises(click.Abort):
            validate_credentials(config)

    def test__validate_credentials__id_and_access_token_succeeds(self):
        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(return_value='foo')

        self.assertIsNone(validate_credentials(config))

    def test__validate_api_key__no_tokens_fails(self):
        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(return_value=None)

        with self.assertRaises(click.Abort):
            validate_api_key(config)

    def test__validate_api_key__exists_succeeds(self):
        config = MagicMock()
        config.auth_store.__getitem__ = MagicMock(return_value='foo')

        self.assertIsNone(validate_api_key(config))

    def test__validate_version__object_fails(self):
        with self.assertRaises(click.Abort):
            validate_version(MagicMock(), {}, 'foo')

    def test__validate_version__text_string_fails(self):
        with self.assertRaises(click.Abort):
            validate_version(MagicMock(), 'foo', 'foo')

    def test__validate_version__huge_number_fails(self):
        with self.assertRaises(click.Abort):
            validate_version(MagicMock(), 3498738943789379832389423942983, 'foo')

    def test__validate_version__negative_number_fails(self):
        with self.assertRaises(click.Abort):
            validate_version(MagicMock(), -1, 'foo')

    def test__validate_version__number_string_succeeds(self):
        self.assertIsNone(validate_version(MagicMock(), '123', 'foo'))

    def test__validate_version__number_succeeds(self):
        self.assertIsNone(validate_version(MagicMock(), 321, 'foo'))
