from cli.config import Config
from cli.internal.commands.command import Command
from cli.version import __version__


class VersionCommand(Command):
    def __init__(self, config: Config):
        self.config = config

    @Command.helper('version')
    def run(self):
        self.config.logger.info('Mason CLI v{}'.format(__version__))
        self.config.logger.info('Copyright (C) 2019 Mason America (https://bymason.com)')
        self.config.logger.info('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')
