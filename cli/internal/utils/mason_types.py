import click


class Version(click.IntRange):
    name = 'version'

    def __init__(self):
        super(Version, self).__init__(min=0)

    def convert(self, value, param, ctx):
        if value == 'latest':
            return value
        else:
            return super(Version, self).convert(value, param, ctx)
