import click


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv:
            return rv

        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class Version(click.IntRange):
    name = 'version'

    def __init__(self):
        super(Version, self).__init__(min=0)

    def convert(self, value, param, ctx):
        if value == 'latest':
            return value
        else:
            return super(Version, self).convert(value, param, ctx)
