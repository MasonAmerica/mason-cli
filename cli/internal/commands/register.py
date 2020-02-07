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

        validate_credentials(config)

    def register_artifact(self, binary, artifact):
        artifact.log_details()
        if not self.config.skip_verify:
            click.confirm('Continue register?', default=True, abort=True)

        self.config.logger.debug('File SHA1: {}'.format(hash_file(binary, 'sha1')))
        self.config.logger.debug('File MD5: {}'.format(hash_file(binary, 'md5')))

        try:
            self.config.api.upload_artifact(binary, artifact)
            self.config.logger.info("{} '{}' registered.".format(
                artifact.get_type().capitalize(), artifact.get_name()))
        except ApiError as e:
            is_in_project_mode = getattr(self.config, 'project_mode', None)
            if is_in_project_mode and e.message and 'already exists' in e.message:
                self.config.logger.info("{} '{}' already registered, ignoring.".format(
                    artifact.get_type().capitalize(), artifact.get_name()))
                pass
            else:
                e.exit(self.config)
                return


class RegisterConfigCommand(RegisterCommand):
    def __init__(self, config, config_files, working_dir=None):
        super(RegisterConfigCommand, self).__init__(config)
        self.config_files = config_files
        self.working_dir = working_dir or tempfile.mkdtemp()

    @Command.log('register config')
    def run(self):
        configs = []

        for num, file in enumerate(self.config_files):
            config = OSConfig.parse(self.config, file)
            config = self._sanitize_config_for_upload(config)
            self.register_artifact(config.binary, config)

            configs.append(config)

            if num + 1 < len(self.config_files):
                self.config.logger.info('')

        return configs

    def _sanitize_config_for_upload(self, config):
        raw_config = copy.deepcopy(config.ecosystem)

        raw_config.pop('from', None)
        try:
            self._maybe_inject_config_version(config, raw_config)
            self._maybe_inject_app_versions(raw_config)
        except ApiError as e:
            e.exit(self.config)

        config_file = os.path.join(self.working_dir, os.path.basename(config.binary))
        with open(config_file, 'w') as f:
            f.write(yaml.safe_dump(raw_config))
        rewritten_config = OSConfig.parse(self.config, config_file)
        rewritten_config.user_binary = config.user_binary
        return rewritten_config

    def _maybe_inject_config_version(self, config, raw_config):
        if config.get_version() == 'latest':
            latest_config = self.config.api.get_latest_artifact(config.get_name(), 'config')
            if latest_config:
                raw_config['os']['version'] = int(latest_config.get('version')) + 1
            else:
                raw_config['os']['version'] = 1

    def _maybe_inject_app_versions(self, raw_config):
        for app in raw_config.get('apps') or []:
            if app.get('version_code') == 'latest':
                latest_apk = self.config.api.get_latest_artifact(app.get('package_name'), 'apk')
                if latest_apk:
                    app['version_code'] = int(latest_apk.get('version'))
                else:
                    self.config.logger.error("Apk '{}' not found, register it first.".format(
                        app.get('package_name')))
                    raise click.Abort()


class RegisterApkCommand(RegisterCommand):
    def __init__(self, config, apk_files):
        super(RegisterApkCommand, self).__init__(config)
        self.apk_files = apk_files

    @Command.log('register apk')
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

    @Command.log('register media')
    def run(self):
        self._maybe_inject_version()
        self.register_artifact(
            self.media_file,
            Media.parse(self.config, self.name, self.type, self.version, self.media_file))

        return {
            'name': self.name,
            'version': self.version
        }

    def _maybe_inject_version(self):
        if self.version != 'latest':
            return

        latest_media = self.config.api.get_latest_artifact(self.name, 'media')
        if latest_media:
            is_in_project_mode = getattr(self.config, 'project_mode', None)
            checksum = latest_media.get('checksum') or {}
            if is_in_project_mode and checksum.get('sha1') == hash_file(self.media_file, 'sha1'):
                self.version = int(latest_media.get('version'))
            else:
                self.version = int(latest_media.get('version')) + 1
        else:
            self.version = 1


class RegisterProjectCommand(RegisterCommand):
    def __init__(self, config, context_file, working_dir=None):
        super(RegisterProjectCommand, self).__init__(config)
        self.context_file = context_file
        self.working_dir = working_dir or tempfile.mkdtemp()

    @Command.log('register project')
    def run(self):
        # Needs to be a local import to prevent recursion
        from cli.internal.commands.stage import StageCommand

        masonrc = self._validated_masonrc()
        context = self._parse_context(masonrc)

        raw_config_files = self._validated_files(context.get('configs') or 'mason.yml', 'yml')
        apk_files = self._validated_files(context.get('apps'), 'apk')
        raw_boot_animations = self._validated_media(context.get('bootanimations'))

        self.config.project_mode = True
        RegisterApkCommand(self.config, apk_files).run()

        boot_animations = []
        for anim in raw_boot_animations:
            self.config.logger.info('')
            result = RegisterMediaCommand(
                self.config, anim.get('name'), 'bootanimation', 'latest', anim.get('file')).run()
            boot_animations.append(result)
        self.config.project_mode = False

        config_files = []
        for raw_config_file in raw_config_files:
            config_files.append(self._rewritten_config(raw_config_file, apk_files, boot_animations))

        self.config.logger.info('')
        StageCommand(self.config, config_files, True, True, None, self.working_dir).run()

    def _validated_masonrc(self):
        masonrc = os.path.join(self.context_file, '.masonrc')

        if not os.path.isfile(masonrc):
            self.config.logger.error(
                ".masonrc file not found. Please run 'mason init' to create the project context.")
            raise click.Abort()

        return masonrc

    def _validated_file(self, path):
        file = self._expanded_path(path)

        if not os.path.isfile(file):
            self.config.logger.error('Project resource does not exist: {}'.format(file))
            raise click.Abort()

        return file

    def _expanded_path(self, path):
        if os.path.isabs(path):
            file = path
        else:
            file = os.path.abspath(os.path.join(self.context_file, path))
        return file

    def _validated_files(self, paths, extension):
        if not paths:
            return []
        elif type(paths) != list:
            paths = [paths]

        files = []

        for file in paths:
            file = self._expanded_path(file)
            if os.path.isdir(file):
                sub_paths = list(map(lambda sub: os.path.join(file, sub), os.listdir(file)))
                sub_paths = list(filter(lambda f: f.endswith('.{}'.format(extension)), sub_paths))
                files.extend(self._validated_files(sub_paths, extension))
            else:
                files.append(self._validated_file(file))

        return files

    def _validated_media(self, media):
        if not media:
            return []

        if type(media) == dict:
            return [{
                'name': media.get('name'),
                'file': self._validated_file(media.get('file'))
            }]
        elif type(media) == list:
            new_media = []
            for medium in media:
                new_media.extend(self._validated_media(medium))
            return new_media
        else:
            self.config.logger.error('Invalid media {}'.format(media))
            raise click.Abort()

    def _parse_context(self, masonrc):
        with open(masonrc, 'r') as f:
            context = yaml.safe_load(f)
            if type(context) is not dict:
                self.config.logger.error('.masonrc file is corrupt.')
                raise click.Abort()
        return context

    def _rewritten_config(self, raw_config_file, apk_files, boot_animations):
        raw_config = OSConfig.parse(self.config, raw_config_file).ecosystem
        config = copy.deepcopy(raw_config)
        apps = raw_config.get('apps') or []
        apks = list(map(lambda apk: Apk.parse(self.config, apk), apk_files))
        media = raw_config.get('media') or {}

        config['from'] = raw_config_file
        for apk in apks:
            package_name = apk.get_name()
            version = apk.get_version()
            self._validate_app_presence(package_name, apps)

            for app in config.get('apps'):
                if package_name == app.get('package_name'):
                    app['version_code'] = int(version)
                    break
        for boot_animation in boot_animations:
            name = boot_animation.get('name')
            version = boot_animation.get('version')
            if self._has_boot_animation_presence(media, name):
                config.get('media').get('bootanimation')['version'] = version

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

    def _has_boot_animation_presence(self, media, name):
        anim = media.get('bootanimation')
        if anim and anim.get('name') == name:
            return True

        self.config.logger.debug(
            "Boot animation '{}' declared in project context not found in project "
            "configuration.".format(name))
