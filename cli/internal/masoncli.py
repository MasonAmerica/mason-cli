import inspect
import time

import click
import packaging.version

from cli.internal.apis.mason import MasonApi
from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError
from cli.internal.utils.remote import RequestHandler
from cli.internal.utils.remote import handle_failed_response
from cli.internal.utils.remote import safe_request
from cli.internal.utils.validation import validate_credentials

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse

from cli import __version__
from cli.internal.models.apk import Apk
from cli.internal.models.media import Media
from cli.internal.models.os_config import OSConfig
from cli.internal.utils.store import Store
from cli.internal.utils.constants import AUTH, ENDPOINTS
from cli.internal.xray import XRay


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

    def set_access_token(self, access_token):
        AUTH['access_token'] = access_token

    def set_id_token(self, id_token):
        AUTH['id_token'] = id_token

    def set_api_key(self, api_key):
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
            if e.message:
                self.config.logger.error(e.message)
            raise click.Abort()

    def _request_user_info(self):
        headers = {'Authorization': 'Bearer {}'.format(AUTH['access_token'])}
        r = safe_request(self.config, 'get', ENDPOINTS['user_info_url'], headers=headers)

        if r.status_code == 200:
            return r.json()
        else:
            handle_failed_response(self.config, r, 'Unable to get user info')

    def _get_validated_customer(self):
        # Get the user info
        user_info_data = self._request_user_info()
        if not user_info_data:
            self.config.logger.error('Customer info not found.')
            raise click.Abort()

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]
        if not customer:
            self.config.logger.critical('Could not retrieve customer information.')
            raise click.Abort()

        return customer

    def build(self, project, version, block, fast_build):
        return self._build_project(project, version, block, fast_build)

    def _build_project(self, project, version, block, fast_build):
        validate_credentials(self.config)

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(AUTH['id_token'])}

        customer = self._get_validated_customer()
        self.config.logger.debug('Queueing build...')

        payload = self._get_build_payload(customer, project, version, fast_build)
        builder_url = ENDPOINTS['builder_url'] + '/{0}/'.format(customer) + 'jobs'

        r = safe_request(self.config, 'post', builder_url, headers=headers, json=payload)
        if r.status_code == 200:
            hostname = urlparse(ENDPOINTS['deploy_url']).hostname
            self.config.logger.info('Build queued.')
            self.config.logger.info('You can see the status of your build at '
                                    'https://{}/controller/projects/{}'.format(hostname, project))

            if block:
                job_url = '{}/{}'.format(builder_url, r.json().get('data').get('submittedAt'))

                # 40 minutes approximately since this doesn't account for the request time
                timeout_seconds = 40 * 60
                time_blocked = 0
                while time_blocked < timeout_seconds:
                    r = safe_request(self.config, 'get', job_url, headers=headers)
                    if not r.status_code == 200:
                        self.config.logger.error('Build status check failed')
                        raise click.Abort()

                    if r.json().get('data').get('status') == 'COMPLETED':
                        self.config.logger.info('Build completed')
                        return

                    self.config.logger.info('Waiting for build to complete...')
                    wait_time = 10 if fast_build else 30
                    time.sleep(wait_time)
                    time_blocked += wait_time

                self.config.logger.error('Timed out waiting for build to complete.')
                raise click.Abort()
        else:
            handle_failed_response(self.config, r, 'Unable to enqueue build')

    @staticmethod
    def _get_build_payload(customer, project, version, fast_build):
        payload = {
            'customer': customer,
            'project': project,
            'version': str(version)
        }
        if fast_build:
            payload['fastBuild'] = fast_build
        return payload

    def deploy(self, item_type, name, version, group, push, no_https):
        if item_type == 'apk':
            self._deploy_apk(name, version, group, push, no_https)
        elif item_type == 'config':
            self._deploy_config(name, version, group, push, no_https)
        elif item_type == 'ota':
            self._deploy_ota(name, version, group, push, no_https)
        else:
            self.config.logger.critical('Unsupported deploy type {}'.format(item_type))
            raise click.Abort()

    def _deploy_apk(self, name, version, group, push, no_https):
        validate_credentials(self.config)
        customer = self._get_validated_customer()

        payload = self._get_deploy_payload(customer, group, name, version, 'apk', push, no_https)
        self._deploy_payload(payload, 'apk')

    def _deploy_config(self, name, version, group, push, no_https):
        validate_credentials(self.config)
        customer = self._get_validated_customer()

        payload = self._get_deploy_payload(customer, group, name, version, 'config', push, no_https)
        self._deploy_payload(payload, 'config')

    def _deploy_ota(self, name, version, group, push, no_https):
        validate_credentials(self.config)
        customer = self._get_validated_customer()

        if name != 'mason-os':
            self.config.logger.warning("Unknown name '{0}' for 'ota' deployments. "
                                       "Forcing it to 'mason-os'".format(name))
            name = 'mason-os'

        payload = self._get_deploy_payload(customer, group, name, version, 'ota', push, no_https)
        self._deploy_payload(payload, 'ota')

    def _deploy_payload(self, payload, type):
        self.config.logger.info('---------- DEPLOY -----------')

        self.config.logger.info('Name: {}'.format(payload['name']))
        self.config.logger.info('Type: {}'.format(payload['type']))
        self.config.logger.info('Version: {}'.format(payload['version']))
        self.config.logger.info('Group: {}'.format(payload['group']))
        self.config.logger.info('Push: {}'.format(payload['push']))
        self.config.logger.debug('Customer: {}'.format(payload['customer']))

        if payload.get('deployInsecure', False):
            self.config.logger.info('')
            self.config.logger.info('***WARNING***')
            self.config.logger.info('--no-https enabled: this deployment will be delivered to '
                                    'devices over HTTP.')
            self.config.logger.info('***WARNING***')

        self.config.logger.info('-----------------------------')

        if not self.config.skip_verify:
            click.confirm('Continue deploy?', default=True, abort=True)

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(AUTH['id_token'])}

        r = safe_request(self.config, 'post',
                         ENDPOINTS['deploy_url'], headers=headers, json=payload)

        if r.status_code == 200:
            if r.text:
                self.config.logger.debug(r.text)
            self.config.logger.info('{}:{} was successfully deployed to {}'.format(
                payload['name'], payload['version'], payload['group']))
        else:
            handle_failed_response(self.config, r, 'Unable to deploy {}'.format(type))

    @staticmethod
    def _get_deploy_payload(customer, group, name, version, item_type, push, no_https):
        payload = {
            'customer': customer,
            'group': group,
            'name': name,
            'version': str(version),
            'type': item_type,
            'push': push
        }
        if no_https:
            payload['deployInsecure'] = no_https
        return payload

    def stage(self, yaml, block, fast_build):
        self.register_os_config(yaml)
        self.build(self.artifact.get_name(), self.artifact.get_version(), block, fast_build)

    def login_token(self, api_key):
        self.set_api_key(api_key)
        AUTH.save()

    def login(self, user, password):
        payload = self._get_auth_payload(user, password)
        r = safe_request(self.config, 'post', ENDPOINTS['auth_url'], json=payload)

        if r.status_code == 200:
            self.set_id_token(r.json().get('id_token'))
            self.set_access_token(r.json().get('access_token'))
            AUTH.save()
        else:
            self.config.logger.error('Failed to authenticate.')
            raise click.Abort()

    def _get_auth_payload(self, user, password):
        return {
            'client_id': ENDPOINTS['client_id'],
            'username': user,
            'password': password,
            'id_token': str(AUTH['id_token']),
            'connection': 'Username-Password-Authentication',
            'grant_type': 'password',
            'scope': 'openid',
            'device': ''
        }

    def logout(self):
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

        except Exception as exc:
            raise click.Abort(exc)
