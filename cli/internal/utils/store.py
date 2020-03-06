import os

import click
import yaml


class Store(object):
    def __init__(self, name: str, fields: dict, dir=None, restore=True):
        self._file = os.path.join(dir or click.get_app_dir('Mason CLI'), name + '.yml')
        self._defaults = fields
        self._fields = {}

        if restore:
            self.restore()

    def save(self):
        if not os.path.exists(os.path.dirname(self._file)):
            os.makedirs(os.path.dirname(self._file))
        with open(self._file, 'w') as f:
            f.write(yaml.safe_dump(self._fields))

    def restore(self):
        if os.path.exists(self._file):
            with open(self._file, 'r') as f:
                yml = yaml.safe_load(f)
                if type(yml) is dict:
                    for (k, v) in yml.items():
                        self[k] = v

    def __getitem__(self, item: str):
        return self._fields.get(item, self._defaults.get(item, None))

    def __setitem__(self, key: str, value):
        if value is None:
            self._fields.pop(key, None)
        else:
            self._fields[key] = value

    def clear(self):
        self._fields = {}
