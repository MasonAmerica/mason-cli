from cli import __version__
from cli.internal.commands.command import Command


class VersionCommand(Command):
    def __init__(self, config):
        self.config = config

    def run(self):
        self.config.logger.info('Mason CLI v{}'.format(__version__))
        self.config.logger.info('Copyright (C) 2019 Mason America (https://bymason.com)')
        self.config.logger.info('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')
