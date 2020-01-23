import abc
import copy
import os
import tempfile

import click
import six
import yaml

from cli.internal.commands.command import Command
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials


@six.add_metaclass(abc.ABCMeta)
class RegisterCommand(Command):
    def __init__(self, config):
        self.config = config

    def register_artifact(self, binary, artifact):
        validate_credentials(self.config)

        artifact.log_details()
        if not self.config.skip_verify:
            click.confirm('Continue register?', default=True, abort=True)

        self.config.logger.debug('File SHA1: {}'.format(hash_file(binary, 'sha1', True)))
        self.config.logger.debug('File MD5: {}'.format(hash_file(binary, 'md5', True)))

        try:
            self.config.api.upload_artifact(binary, artifact)
            self.config.logger.info("{} '{}' registered.".format(
                artifact.get_type().capitalize(), artifact.get_name()))
        except ApiError as e:
            if self.config.force and e.message and 'already exists' in e.message:
                self.config.logger.info("{} '{}' already registered, ignoring.".format(
                    artifact.get_type().capitalize(), artifact.get_name()))
                pass
            else:
                e.exit(self.config)
                return


class RegisterConfigCommand(RegisterCommand):
    def __init__(self, config, config_files):
        super(RegisterConfigCommand, self).__init__(config)
        self.config_files = config_files

    def run(self):
        for num, file in enumerate(self.config_files):
            config = OSConfig.parse(self.config, file)
            self._sanitize_config_for_upload(config)
            self.register_artifact(file, config)

            if num + 1 < len(self.config_files):
                self.config.logger.info('')

    def _sanitize_config_for_upload(self, config):
        raw_config = copy.deepcopy(config.ecosystem)
        prev = raw_config.pop('from', None)
        if prev:
            with open(config.binary, 'w') as f:
                f.write(yaml.safe_dump(raw_config))


class RegisterApkCommand(RegisterCommand):
    def __init__(self, config, apk_files):
        super(RegisterApkCommand, self).__init__(config)
        self.apk_files = apk_files

    def run(self):
        for num, file in enumerate(self.apk_files):
            self.register_artifact(file, Apk.parse(self.config, file))

            if num + 1 < len(self.apk_files):
                self.config.logger.info('')


class RegisterMediaCommand(RegisterCommand):
    def __init__(self, config, name, type, version, media_file):
        super(RegisterMediaCommand, self).__init__(config)
        self.name = name
        self.type = type
        self.version = version
        self.media_file = media_file

    def run(self):
        self.register_artifact(
            self.media_file,
            Media.parse(self.config, self.name, self.type, self.version, self.media_file))


class RegisterProjectCommand(RegisterCommand):
    def __init__(self, config, context_file, working_dir=tempfile.mkdtemp()):
        super(RegisterProjectCommand, self).__init__(config)
        self.context_file = context_file
        self.working_dir = working_dir

    def run(self):
        # Needs to be a local import to prevent recursion
        from cli.internal.commands.stage import StageCommand

        masonrc = self._validated_masonrc()
        context = self._parse_context(masonrc)

        raw_config_files = self._validated_files(context.get('configs') or 'mason.yml', 'yml')
        apk_files = self._validated_files(context.get('apps'), 'apk')
        config_files = []
        for raw_config_file in raw_config_files:
            config_files.append(self._rewritten_config(raw_config_file, apk_files))

        self.config.force = True
        RegisterApkCommand(self.config, apk_files).run()
        self.config.force = False

        self.config.logger.info('')
        StageCommand(self.config, config_files, True, True, None).run()

    def _validated_masonrc(self):
        masonrc = os.path.join(self.context_file, '.masonrc')

        if not os.path.isfile(masonrc):
            self.config.logger.error(
                ".masonrc file not found. Please run 'mason init' to create the project context.")
            raise click.Abort()

        return masonrc

    def _validated_file(self, path):
        if os.path.isabs(path):
            file = path
        else:
            file = os.path.abspath(os.path.join(self.context_file, path))

        if not os.path.isfile(file):
            self.config.logger.error('Project resource does not exist: {}'.format(file))
            raise click.Abort()

        return file

    def _validated_files(self, paths, extension):
        if not paths:
            return []
        elif type(paths) != list:
            paths = [paths]

        files = []

        for file in paths:
            if os.path.isdir(file):
                sub_paths = list(map(lambda sub: os.path.join(file, sub), os.listdir(file)))
                sub_paths = list(filter(lambda f: f.endswith('.{}'.format(extension)), sub_paths))
                files.extend(self._validated_files(sub_paths, extension))
            else:
                files.append(self._validated_file(file))

        return files

    def _parse_context(self, masonrc):
        with open(masonrc, 'r') as f:
            context = yaml.safe_load(f)
            if type(context) is not dict:
                self.config.logger.error('.masonrc file is corrupt.')
                raise click.Abort()
        return context

    def _rewritten_config(self, raw_config_file, apk_files):
        raw_config = OSConfig.parse(self.config, raw_config_file).ecosystem
        config = copy.deepcopy(raw_config)
        apps = raw_config.get('apps') or []
        apks = list(map(lambda apk: Apk.parse(self.config, apk), apk_files))

        config['from'] = raw_config_file
        for apk in apks:
            package_name = apk.get_name()
            version = apk.get_version()
            self._validate_app_presence(package_name, apps)

            for app in config.get('apps'):
                if package_name == app.get('package_name'):
                    app['version_code'] = int(version)
                    break

        config_file = os.path.join(self.working_dir, os.path.basename(raw_config_file))
        with open(config_file, 'w') as f:
            f.write(yaml.safe_dump(config))
        return config_file

    def _validate_app_presence(self, package_name, apps):
        for app in apps:
            if package_name == app.get('package_name'):
                return

        self.config.logger.error(
            "App '{}' declared in project context not found in project "
            "configuration.".format(package_name))
        raise click.Abort()
