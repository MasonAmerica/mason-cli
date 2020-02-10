import tempfile

from cli.internal.commands.build import BuildCommand
from cli.internal.commands.command import Command
from cli.internal.commands.register import RegisterConfigCommand


class StageCommand(Command):
    def __init__(
        self,
        config,
        config_files,
        block,
        turbo,
        mason_version,
        working_dir=None
    ):
        self.config = config
        self.config_files = config_files
        self.block = block
        self.turbo = turbo
        self.mason_version = mason_version
        self.working_dir = working_dir or tempfile.mkdtemp()

    @Command.helper('stage')
    def run(self):
        for num, file in enumerate(self.config_files):
            register_command = RegisterConfigCommand(self.config, [file], self.working_dir)
            artifact = register_command.run()[0]

            build_command = BuildCommand(
                self.config,
                artifact.get_name(),
                artifact.get_version(),
                self.block,
                self.turbo,
                self.mason_version)

            self.config.logger.info('')
            build_command.run()

            if num + 1 < len(self.config_files):
                self.config.logger.info('')
