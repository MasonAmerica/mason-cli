import abc
import copy
import os
import tempfile
from abc import abstractmethod
from threading import Lock

import click
import six
import yaml
from tqdm import tqdm

from cli.config import Config
from cli.internal.commands.command import Command
from cli.internal.models.apk import Apk
from cli.internal.models.artifacts import IArtifact
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.io import wait_for_futures
from cli.internal.utils.remote import ApiError
from cli.internal.utils.validation import validate_credentials


@six.add_metaclass(abc.ABCMeta)
class RegisterCommand(Command):
    def __init__(self, config: Config):
        super(RegisterCommand, self).__init__(config)

        validate_credentials(config)

    def run(self):
        (artifacts, *args) = self.prepare()

        self.show_operations(artifacts)
        if self.request_confirmation():
            self.register(*args)

        return (artifacts, *args)

    @abstractmethod
    def prepare(self):
        pass

    def show_operations(self, artifacts: list):
        for artifact in artifacts:
            artifact.log_details()
            self.config.logger.info('')

    def request_confirmation(self):
        if not self.config.execute_ops:
            return False
        if not self.config.skip_verify:
            click.confirm('Continue registration?', default=True, abort=True)

        return True

    @abstractmethod
    def register(self, *args):
        pass

    def register_artifact(self, binary, artifact: IArtifact):
        if getattr(artifact, 'already_registered', None):
            with tqdm.external_write_mode(nolock=True):
                self.config.logger.info("{} '{}' already registered, ignoring.".format(
                    artifact.get_pretty_type(), artifact.get_name()))
            return

        try:
            self.config.api.upload_artifact(binary, artifact)
        except ApiError as e:
            if e.message and 'already exists' in e.message:
                raise ApiError(
                    "{} '{}' at version {} has already been registered and cannot be "
                    "overwritten.".format(
                        artifact.get_pretty_type(), artifact.get_name(), artifact.get_version()))
            else:
                raise e

        with tqdm.external_write_mode(nolock=True):
            self.config.logger.info("{} '{}' registered.".format(
                artifact.get_pretty_type(), artifact.get_name()))


class RegisterConfigCommand(RegisterCommand):
    def __init__(self, config: Config, config_files: list, working_dir=None):
        super(RegisterConfigCommand, self).__init__(config)
        self.config_files = config_files
        self.working_dir = working_dir or tempfile.mkdtemp()

    @Command.helper('register config')
    def run(self):
        return super(RegisterConfigCommand, self).run()

    def prepare(self):
        configs = []

        for file in self.config_files:
            config = OSConfig.parse(self.config, file)
            config = self._sanitize_config_for_upload(config)

            self.config.analytics.log_config(config.ecosystem)
            configs.append(config)

        return configs, configs

    def register(self, configs):
        register_ops = []

        for config in configs:
            register_ops.append(self.config.executor.submit(
                self.register_artifact, config.binary, config))

        wait_for_futures(self.config.executor, register_ops)

    def _sanitize_config_for_upload(self, config: OSConfig):
        raw_config = copy.deepcopy(config.ecosystem)
        raw_config.pop('from', None)

        lock = Lock()
        rewrite_ops = []

        rewrite_ops.append(self.config.executor.submit(
            self._maybe_inject_config_version, lock, config, raw_config))
        for app in raw_config.get('apps') or []:
            rewrite_ops.append(self.config.executor.submit(
                self._maybe_inject_app_version, lock, app))
        rewrite_ops.append(self.config.executor.submit(
            self._maybe_inject_media_versions, lock, raw_config))

        wait_for_futures(self.config.executor, rewrite_ops)

        config_file = os.path.join(self.working_dir, os.path.basename(config.binary))
        with open(config_file, 'w') as f:
            f.write(yaml.safe_dump(raw_config))
        rewritten_config = OSConfig.parse(self.config, config_file)
        rewritten_config.user_binary = config.user_binary
        return rewritten_config

    def _maybe_inject_config_version(self, lock: Lock, config: OSConfig, raw_config: dict):
        if config.get_version() != 'latest':
            return

        latest_config = self.config.api.get_highest_artifact('config', config.get_name())
        with lock:
            if latest_config:
                raw_config['os']['version'] = int(latest_config.get('version')) + 1
            else:
                raw_config['os']['version'] = 1

    def _maybe_inject_app_version(self, lock: Lock, app: dict):
        if app and app.get('version_code') == 'latest':
            latest_apk = self.config.api.get_latest_artifact(app.get('package_name'), 'apk')
            if latest_apk:
                with lock:
                    app['version_code'] = int(latest_apk.get('version'))
            else:
                self.config.logger.error("Apk '{}' not found, register it first.".format(
                    app.get('package_name')))
                raise click.Abort()

    def _maybe_inject_media_versions(self, lock: Lock, raw_config: dict):
        media = raw_config.get('media') or {}
        boot_anim = media.get('bootanimation') or {}

        if boot_anim.get('version') != 'latest':
            return

        latest_anim = self.config.api.get_latest_artifact(boot_anim.get('name'), 'media')
        if latest_anim:
            with lock:
                boot_anim['version'] = int(latest_anim.get('version'))
        else:
            self.config.logger.error("Boot animation '{}' not found, register it first.".format(
                boot_anim.get('name')))
            raise click.Abort()


class RegisterApkCommand(RegisterCommand):
    def __init__(self, config: Config, apk_files: list):
        super(RegisterApkCommand, self).__init__(config)
        self.apk_files = apk_files

    @Command.helper('register apk')
    def run(self):
        return super(RegisterApkCommand, self).run()

    def prepare(self):
        prepare_ops = self.start_prepare_ops()
        apks = wait_for_futures(self.config.executor, prepare_ops)
        return apks, apks

    def register(self, apks):
        register_ops = self.start_register_ops(apks)
        wait_for_futures(self.config.executor, register_ops)

    def start_prepare_ops(self):
        apk_ops = []

        for file in self.apk_files:
            apk_ops.append(self.config.executor.submit(self.prepare_apk, file))

        return apk_ops

    def start_register_ops(self, apks):
        register_ops = []

        for apk in apks:
            register_ops.append(self.config.executor.submit(
                self.register_artifact, apk.binary, apk))

        return register_ops

    def prepare_apk(self, binary):
        apk = Apk.parse(self.config, binary)

        is_in_project_mode = getattr(self.config, 'project_mode', None)
        if is_in_project_mode:
            try:
                apk_artifact = self.config.api.get_artifact(
                    apk.get_type(), apk.get_name(), apk.get_version())
            except ApiError as e:
                self.config.logger.debug(e, exc_info=True)
                apk_artifact = {}

            checksum = apk_artifact.get('checksum') or {}
            if checksum.get('sha1') == hash_file(binary, 'sha1'):
                apk.already_registered = True

        return apk


class RegisterMediaCommand(RegisterCommand):
    def __init__(self, config: Config, name: str, type: str, version: str, media_file):
        super(RegisterMediaCommand, self).__init__(config)
        self.name = name
        self.type = type
        self.version = version
        self.media_file = media_file

        self.already_registered = False

    @Command.helper('register media')
    def run(self):
        return super(RegisterMediaCommand, self).run()

    def prepare(self):
        self._maybe_inject_version()
        media = Media.parse(self.config, self.name, self.type, self.version, self.media_file)
        media.already_registered = self.already_registered

        return [media], media

    def register(self, media):
        self.register_artifact(self.media_file, media)

    def _maybe_inject_version(self):
        if self.version != 'latest':
            return

        latest_media = self.config.api.get_highest_artifact('media', self.name)
        if latest_media:
            is_in_project_mode = getattr(self.config, 'project_mode', None)
            checksum = latest_media.get('checksum') or {}
            if is_in_project_mode and checksum.get('sha1') == hash_file(self.media_file, 'sha1'):
                self.version = int(latest_media.get('version'))
                self.already_registered = True
            else:
                self.version = int(latest_media.get('version')) + 1
        else:
            self.version = 1


class RegisterProjectCommand(RegisterCommand):
    def __init__(self, config: Config, context_file, working_dir=None):
        super(RegisterProjectCommand, self).__init__(config)
        self.context_file = context_file
        self.working_dir = working_dir or tempfile.mkdtemp()

    @Command.helper('register project')
    def run(self):
        self.config.project_mode = True
        results = super(RegisterProjectCommand, self).run()
        self.config.project_mode = False

        return results

    def prepare(self):
        # Needs to be a local import to prevent recursion
        from cli.internal.commands.stage import StageCommand

        masonrc = self._validated_masonrc()
        context = self._parse_context(masonrc)

        raw_config_files = self._validated_files(context.get('configs') or 'mason.yml', 'yml')
        apk_files = self._validated_files(context.get('apps'), 'apk')
        raw_boot_animations = self._validated_media(context.get('bootanimations'))

        apk_registration = RegisterApkCommand(self.config, apk_files)
        anim_registrations = []
        for anim in raw_boot_animations:
            anim_registrations.append(RegisterMediaCommand(
                self.config, anim.get('name'), 'bootanimation', 'latest', anim.get('file')))

        apk_preps = apk_registration.start_prepare_ops()
        media_preps = []
        for reg in anim_registrations:
            media_preps.append(self.config.executor.submit(reg.prepare))

        apks = wait_for_futures(self.config.executor, apk_preps)
        media_artifacts = []
        for prep in wait_for_futures(self.config.executor, media_preps):
            media_artifacts.append(prep[1])

        config_files = []
        for raw_config_file in raw_config_files:
            config_files.append(self._rewritten_config(raw_config_file, apks, media_artifacts))
        stage = StageCommand(self.config, config_files, True, None, self.working_dir)

        stage_prep = stage.prepare()
        configs = stage_prep[0]
        register = stage_prep[2]

        return [*apks, *media_artifacts, *configs], \
            apk_registration, apks, \
            anim_registrations, media_artifacts, \
            stage, configs, register

    def register(
        self,
        apk_registration: RegisterApkCommand,
        apks: list,
        anim_registrations: list,
        media_artifacts: list,
        stage,
        configs: list,
        register: RegisterConfigCommand
    ):
        register_ops = apk_registration.start_register_ops(apks)
        for num, anim in enumerate(anim_registrations):
            register_ops.append(self.config.executor.submit(anim.register, media_artifacts[num]))

        wait_for_futures(self.config.executor, register_ops)

        stage.register(configs, register)

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
            if not file:
                continue

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
        with open(masonrc, encoding='utf-8-sig') as f:
            context = yaml.safe_load(f)
            if type(context) is not dict:
                self.config.logger.error('.masonrc file is corrupt.')
                raise click.Abort()
        return context

    def _rewritten_config(self, raw_config_file, apks, medias):
        raw_config = OSConfig.parse(self.config, raw_config_file).ecosystem
        config = copy.deepcopy(raw_config)
        apps = raw_config.get('apps') or []
        media = raw_config.get('media') or {}

        config['from'] = raw_config_file
        for apk in apks:
            package_name = apk.get_name()
            version = apk.get_version()

            if self._has_app_presence(package_name, apps):
                for app in config.get('apps'):
                    if package_name == app.get('package_name'):
                        app['version_code'] = int(version)
                        break

        for medium in medias:
            name = medium.get_name()
            version = medium.get_version()
            if self._has_boot_animation_presence(media, name):
                config.get('media').get('bootanimation')['version'] = int(version)

        config_file = os.path.join(self.working_dir, os.path.basename(raw_config_file))
        with open(config_file, 'w') as f:
            f.write(yaml.safe_dump(config))
        return config_file

    def _has_app_presence(self, package_name, apps):
        for app in apps:
            if app and package_name == app.get('package_name'):
                return True

        self.config.logger.debug(
            "App '{}' declared in project context not found in project "
            "configuration.".format(package_name))

    def _has_boot_animation_presence(self, media, name):
        anim = media.get('bootanimation')
        if anim and anim.get('name') == name:
            return True

        self.config.logger.debug(
            "Boot animation '{}' declared in project context not found in project "
            "configuration.".format(name))
