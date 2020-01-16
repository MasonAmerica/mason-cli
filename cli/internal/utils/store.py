import os

import click
import yaml


class Store(object):
    def __init__(self, name, fields):
        self.file = os.path.join(click.get_app_dir('Mason CLI'), name + '.yml')
        self.defaults = fields
        self.fields = {}

        self.restore()

    def save(self):
        if not os.path.exists(os.path.dirname(self.file)):
            os.makedirs(os.path.dirname(self.file))
        with open(self.file, 'w') as f:
            f.write(yaml.safe_dump(self.fields))

    def restore(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                yml = yaml.safe_load(f)
                if yml:
                    for (k, v) in yml.items():
                        self.fields[k] = v

    def __getitem__(self, item):
        return self.fields.get(item, self.defaults.get(item, None))

    def __setitem__(self, key, value):
        self.fields[key] = value

    def clear(self):
        self.fields = {}
