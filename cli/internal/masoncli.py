import inspect
import time

import click
import packaging.version

from cli import __version__
from cli.internal.apis.mason import MasonApi
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.constants import AUTH
from cli.internal.utils.constants import ENDPOINTS
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError
from cli.internal.utils.remote import RequestHandler
from cli.internal.utils.remote import safe_request
from cli.internal.utils.store import Store
from cli.internal.utils.validation import validate_credentials
from cli.internal.xray import XRay

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse


class MasonCli:
    def __init__(self, config):
        self.config = config
        self.api = MasonApi(RequestHandler(config), AUTH, ENDPOINTS)
        self.artifact = None

    def check_for_updates(self):
        current_time = int(time.time())
        cache = Store('version-check-cache', {'timestamp': 0})

        if current_time - cache['timestamp'] < 86400:  # 1 day
            self.config.logger.debug('Skipped version check')
            return
        cache['timestamp'] = current_time
        cache.save()

        self.config.logger.debug('Checking for updates')
        try:
            r = safe_request(
                self.config, 'get',
                'https://raw.githubusercontent.com/MasonAmerica/mason-cli/master/VERSION')
        except click.Abort:
            # Don't fail the command if checking for updates fails.
            return

        if r.status_code == 200 and r.text:
            current_version = packaging.version.parse(__version__)
            remote_version = packaging.version.parse(r.text)
            if remote_version > current_version:
                self.config.logger.info(inspect.cleandoc("""
                ==================== NOTICE ====================
                A newer version (v{}) of the Mason CLI is available.

                Download the latest version:
                https://github.com/MasonAmerica/mason-cli/releases/latest

                And check out our installation guide:
                http://docs.bymason.com/mason-cli/#install
                ==================== NOTICE ====================
                """.format(remote_version)))
                self.config.logger.info('')
        else:
            self.config.logger.debug('Failed to check for updates: {}'.format(r))

    @staticmethod
    def set_access_token(access_token):
        AUTH['access_token'] = access_token

    @staticmethod
    def set_id_token(id_token):
        AUTH['id_token'] = id_token

    @staticmethod
    def set_api_key(api_key):
        AUTH['api_key'] = api_key

    def register_os_config(self, config):
        self.artifact = OSConfig.parse(self.config, config)
        self._register_artifact(config)

    def register_apk(self, apk):
        self.artifact = Apk.parse(self.config, apk)
        self._register_artifact(apk)

    def register_media(self, name, type, version, media):
        self.artifact = Media.parse(self.config, name, type, version, media)
        self._register_artifact(media)

    def build(self, project, version, block, fast_build):
        return self._build_project(project, version, block, fast_build)

    def stage(self, yaml, block, fast_build):
        self.register_os_config(yaml)
        self.build(self.artifact.get_name(), self.artifact.get_version(), block, fast_build)

    def deploy(self, item_type, name, version, group, push, no_https):
        validate_credentials(self.config)
        if item_type == 'apk':
            self._deploy_apk(name, version, group, push, no_https)
        elif item_type == 'config':
            self._deploy_config(name, version, group, push, no_https)
        elif item_type == 'ota':
            self._deploy_ota(name, version, group, push, no_https)
        else:
            self.config.logger.critical('Unsupported deploy type {}'.format(item_type))
            raise click.Abort()

    def login_token(self, api_key):
        self.set_api_key(api_key)
        AUTH.save()

    def login(self, username, password):
        try:
            user = self.api.login(username, password)
        except ApiError as e:
            self._handle_api_error(e)
            return

        self.set_id_token(user.get('id_token'))
        self.set_access_token(user.get('access_token'))
        AUTH.save()

    @staticmethod
    def logout():
        AUTH.clear()
        AUTH.save()

    def xray(self, device, service, command, local=None, remote=None, args=None):
        key = AUTH['api_key']
        if not key:
            self.config.logger.error(
                'Please set an API key with \'mason login --api-key\' to use X-Ray.')
            raise click.Abort()

        if args is None:
            args = []
        else:
            args = list(args)

        try:
            self._xray(args, command, device, local, remote, service)
        except Exception as exc:
            raise click.Abort(exc)

    def _register_artifact(self, binary):
        validate_credentials(self.config)
        if not self.config.skip_verify:
            click.confirm('Continue register?', default=True, abort=True)

        self.config.logger.debug('File SHA1: {}'.format(hash_file(binary, 'sha1', True)))
        self.config.logger.debug('File MD5: {}'.format(hash_file(binary, 'md5', True)))

        try:
            self.api.upload_artifact(binary, self.artifact)
            self.config.logger.info('Artifact registered.')
        except ApiError as e:
            self._handle_api_error(e)
            return

    def _deploy_apk(self, name, version, group, push, no_https):
        self._deploy_artifact('apk', name, version, group, push, no_https)

    def _deploy_config(self, name, version, group, push, no_https):
        self._deploy_artifact('config', name, version, group, push, no_https)

    def _deploy_ota(self, name, version, group, push, no_https):
        if name != 'mason-os':
            self.config.logger.warning("Unknown name '{0}' for 'ota' deployments. "
                                       "Forcing it to 'mason-os'".format(name))
            name = 'mason-os'

        self._deploy_artifact('ota', name, version, group, push, no_https)

    def _deploy_artifact(self, type, name, version, group, push, no_https):
        self.config.logger.info('---------- DEPLOY -----------')

        self.config.logger.info('Name: {}'.format(name))
        self.config.logger.info('Type: {}'.format(type))
        self.config.logger.info('Version: {}'.format(version))
        self.config.logger.info('Group: {}'.format(group))
        self.config.logger.info('Push: {}'.format(push))

        if no_https:
            self.config.logger.info('')
            self.config.logger.info('***WARNING***')
            self.config.logger.info('--no-https enabled: this deployment will be delivered to '
                                    'devices over HTTP.')
            self.config.logger.info('***WARNING***')

        self.config.logger.info('-----------------------------')

        if not self.config.skip_verify:
            click.confirm('Continue deploy?', default=True, abort=True)

        try:
            self.api.deploy_artifact(type, name, version, group, push, no_https)
            self.config.logger.info('Artifact deployed.')
        except ApiError as e:
            self._handle_api_error(e)
            return

    def _build_project(self, project, version, block, fast_build):
        validate_credentials(self.config)

        try:
            build = self.api.start_build(project, version, fast_build)
        except ApiError as e:
            self._handle_api_error(e)
            return

        self.config.logger.info('Build queued.')
        self.config.logger.info(
            'You can see the status of your build at '
            'https://{}/controller/projects/{}'.format(
                urlparse(ENDPOINTS['deploy_url']).hostname, project))

        if block:
            # 40 minutes (*approximately* since this doesn't account for the request time)
            timeout_seconds = 40 * 60
            time_blocked = 0
            while time_blocked < timeout_seconds:
                try:
                    build = self.api.get_build(build.get('data').get('submittedAt'))
                except ApiError as e:
                    self.config.logger.error('Build status check failed.')
                    self._handle_api_error(e)
                    return

                if build.get('data').get('status') == 'COMPLETED':
                    self.config.logger.info('Build completed.')
                    return

                self.config.logger.info('Waiting for build to complete...')
                wait_time = 10 if fast_build else 30
                time.sleep(wait_time)
                time_blocked += wait_time

            self.config.logger.error('Timed out waiting for build to complete.')
            raise click.Abort()

    def _xray(self, args, command, device, local, remote, service):
        xray = XRay(device, self.config.logger)

        if service == "adb":
            if command == "logcat":
                xray.logcat(args)
            elif command == "shell":
                xray.shell(args)
            elif command == "push":
                xray.push(local, remote)
            elif command == "pull":
                xray.pull(remote, dest_file=local)
            elif command == "install":
                xray.install(local, args)
            elif command == "uninstall":
                xray.uninstall(remote, args)
            else:
                raise click.UsageError("Unknown adb command %s" % command)
        elif service == "vnc":
            if command == "desktop":
                xray.desktop(local)
            else:
                raise click.UsageError("Unknown vnc command %s" % command)
        else:
            raise click.UsageError("Unknown service %s" % service)

    def _handle_api_error(self, e):
        if e.message:
            self.config.logger.error(e.message)
        raise click.Abort()
