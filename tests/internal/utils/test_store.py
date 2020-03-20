import os
import unittest

import yaml
from click.testing import CliRunner

from cli.internal.utils.store import Store


class StoreTest(unittest.TestCase):
    def setUp(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            self.store = Store('test', {'default': True}, os.path.abspath(''), False)

    def test__getset__field_can_be_retrieved(self):
        self.store['key'] = 'value'

        self.assertEqual(self.store['key'], 'value')

    def test__getset__default_can_be_retrieved(self):
        self.assertEqual(self.store['default'], True)

    def test__getset__default_can_be_overwritten(self):
        self.store['default'] = False

        self.assertEqual(self.store['default'], False)

    def test__restore__garbage_file_is_ignored(self):
        self._write_data('foobar')
        self.store['key'] = 'value'

        self.store.restore()

        self.assertDictEqual(self.store._fields, {'key': 'value'})

    def test__restore__existing_fields_are_overwritten(self):
        self._write_data({'key': 'new value'})
        self.store['key'] = 'value'

        self.store.restore()

        self.assertDictEqual(self.store._fields, {'key': 'new value'})

    def test__restore__new_fields_are_merged(self):
        self._write_data({'otherKey': 'other value'})
        self.store['key'] = 'value'

        self.store.restore()

        self.assertDictEqual(self.store._fields, {'key': 'value', 'otherKey': 'other value'})

    def test__restore__fields_are_initialized(self):
        self._write_data({'key': 'value'})

        self.store.restore()

        self.assertDictEqual(self.store._fields, {'key': 'value'})

    def test__save__fields_are_stored(self):
        self.store['key'] = 'value'

        self.store.save()
        self.store.clear()
        self.store.restore()

        self.assertDictEqual(self.store._fields, {'key': 'value'})

    def test__save__defaults_are_ignored(self):
        self.store['default'] = False

        self.store.save()
        self.store.clear()
        self.store.restore()

        self.assertDictEqual(self.store._fields, {'default': False})

    def test__clear__fields_are_wiped(self):
        self.store['key'] = 'value'

        self.store.clear()

        self.assertDictEqual(self.store._fields, {})

    def test__clear__defaults_are_ignored(self):
        self.store['key'] = 'value'

        self.store.clear()

        self.assertDictEqual(self.store._defaults, {'default': True})

    def _write_data(self, data):
        os.makedirs(os.path.dirname(self.store._file), exist_ok=True)
        with open(self.store._file, 'w') as f:
            if type(data) is dict:
                yaml.safe_dump(data, f)
            else:
                f.write(data)
