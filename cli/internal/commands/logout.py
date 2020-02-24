from cli.config import Config
from cli.internal.commands.command import Command


class LogoutCommand(Command):
    def __init__(self, config: Config):
        self.config = config

    @Command.helper('logout')
    def run(self):
        self.config.auth_store.clear()
        self.config.auth_store.save()
        self.config.logger.info('Successfully logged out.')
