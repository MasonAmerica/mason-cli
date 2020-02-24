import click

from cli.internal.commands.command import Command
from cli.mason import Config


class HelpCommand(Command):
    def __init__(self, config: Config, commands: list):
        self.config = config
        self.commands = commands

    @Command.helper('help')
    def run(self):
        # Local import to prevent recursion
        from cli.mason import cli

        ctx = click.get_current_context()

        if not self.commands:
            self.config.logger.info(cli.get_help(ctx))
            return

        sub_command = cli
        for command_name in self.commands:
            if issubclass(sub_command.__class__, click.MultiCommand):
                sub_command = sub_command.get_command(ctx, command_name)
            else:
                sub_command = None

            if not sub_command:
                raise click.BadArgumentUsage('No such command "{}".'.format(command_name))

        self.config.logger.info(sub_command.get_help(ctx))
