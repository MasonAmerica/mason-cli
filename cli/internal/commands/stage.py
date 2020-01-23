from cli.internal.commands.build import BuildCommand
from cli.internal.commands.command import Command
from cli.internal.commands.register import RegisterConfigCommand
from cli.internal.models.os_config import OSConfig


class StageCommand(Command):
    def __init__(self, config, config_files, block, turbo, mason_version):
        self.config = config
        self.config_files = config_files
        self.block = block
        self.turbo = turbo
        self.mason_version = mason_version

    def run(self):
        for num, file in enumerate(self.config_files):
            artifact = OSConfig.parse(self.config, file)
            register_command = RegisterConfigCommand(self.config, [file])
            build_command = BuildCommand(
                self.config,
                artifact.get_name(),
                artifact.get_version(),
                self.block,
                self.turbo,
                self.mason_version)

            register_command.run()
            self.config.logger.info('')
            build_command.run()

            if num + 1 < len(self.config_files):
                self.config.logger.info('')
