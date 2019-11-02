import base64
import os.path
import time

import click

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse

import requests
from tqdm import tqdm

from masonlib.imason import IMason
from masonlib.internal.apk import Apk
from masonlib.internal.media import Media
from masonlib.internal.os_config import OSConfig
from masonlib.internal.persist import Persist
from masonlib.internal.store import Store
from masonlib.internal.utils import hash_file, log_failed_response


class Mason(IMason):
    """ Base implementation of IMason interface."""

    def __init__(self, config):
        self.config = config
        self.id_token = None
        self.access_token = None
        self.artifact = None
        self.persist = Persist('.masonrc')
        self.store = Store(os.path.join(os.path.expanduser('~'), '.mason.yml'))

    def set_access_token(self, access_token):
        self.access_token = access_token

    def set_id_token(self, id_token):
        self.id_token = id_token

    def _validate_credentials(self):
        self.id_token = self.persist.retrieve_id_token()
        self.access_token = self.persist.retrieve_access_token()

        if not self.id_token or not self.access_token:
            self.config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
            return False

        return True

    def parse_apk(self, apk):
        apk = Apk.parse(self.config, apk)

        if not apk:
            return False

        self.artifact = apk
        return True

    def parse_media(self, name, type, version, binary):
        media = Media.parse(self.config, name, type, version, binary)

        if not media:
            return False

        self.artifact = media
        return True

    def parse_os_config(self, config_yaml):
        os_config = OSConfig.parse(self.config, config_yaml)

        if not os_config:
            return False

        self.artifact = os_config
        return True

    def register(self, binary):
        if not self.config.skip_verify:
            if not click.confirm('Continue register?', default=True):
                self.config.logger.debug('Artifact registration aborted.')
                return False

        if not self._validate_credentials():
            return False

        if not self._register_artifact(binary):
            self.config.logger.error('Unable to register artifact')
            return False

        return True

    def _register_artifact(self, binary):
        sha1 = hash_file(binary, 'sha1', True)
        md5 = hash_file(binary, 'md5', False)

        self.config.logger.debug('File SHA1: {}'.format(sha1))
        self.config.logger.debug('File MD5: {}'.format(hash_file(binary, 'md5', True)))

        customer = self._get_customer()
        if not customer:
            return False

        # Get the signed url data for the user and artifact
        signed_url_data = self._request_signed_url(customer, self.artifact, md5)

        if not signed_url_data:
            return False

        # Get the signed request url from the response
        signed_request_url = signed_url_data['signed_request']

        # Store the download url for mason registry
        download_url = signed_url_data['url']

        # Upload the artifact to the signed url
        if not self._upload_to_signed_url(signed_request_url, binary, self.artifact, md5):
            return False

        # Publish to mason services
        if not self._register_to_mason(customer, download_url, sha1, self.artifact):
            return False

        return True

    def _request_user_info(self):
        headers = {'Authorization': 'Bearer {}'.format(self.access_token)}
        r = requests.get(self.store.user_info_url(), headers=headers)

        if r.status_code == 200:
            return r.json()
        else:
            log_failed_response(self.config, r, 'Unable to get user info')
            return None

    def _get_customer(self):
        # Get the user info
        user_info_data = self._request_user_info()

        if not user_info_data:
            return None

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]
        if not customer:
            self.config.logger.critical('Could not retrieve customer information.')
        return customer

    def _request_signed_url(self, customer, artifact_data, md5):
        self.config.logger.debug('Connecting to server...')
        headers = self._get_signed_url_request_headers(md5)
        url = self._get_signed_url_request_endpoint(customer, artifact_data)

        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            log_failed_response(self.config, r, 'Unable to get signed url')
            return None

    def _get_signed_url_request_headers(self, md5):
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        return {'Content-Type': 'application/json',
                'Content-MD5': base64encodedmd5,
                'Authorization': 'Bearer {}'.format(self.id_token)}

    def _get_signed_url_request_endpoint(self, customer, artifact_data):
        return self.store.registry_signer_url() \
               + '/{0}/{1}/{2}?type={3}'.format(customer, artifact_data.get_name(),
                                                artifact_data.get_version(),
                                                artifact_data.get_type())

    def _upload_to_signed_url(self, url, artifact, artifact_data, md5):
        self.config.logger.debug('Uploading artifact...')
        headers = self._get_signed_url_post_headers(artifact_data, md5)
        artifact_file = open(artifact, 'rb')
        iterable = UploadInChunks(artifact_file.name, chunksize=10)

        r = requests.put(url, data=IterableToFileAdapter(iterable), headers=headers)
        if r.status_code == 200:
            self.config.logger.debug('File upload complete.')
            return True
        else:
            log_failed_response(self.config, r, 'Unable to upload to signed url')
            return False

    @staticmethod
    def _get_signed_url_post_headers(artifact_data, md5):
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        return {'Content-Type': artifact_data.get_content_type(),
                'Content-MD5': base64encodedmd5}

    def _register_to_mason(self, customer, download_url, sha1, artifact_data):
        self.config.logger.debug('Registering to mason services...')
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.id_token)}
        payload = self._get_registry_payload(customer, download_url, sha1, artifact_data)

        if artifact_data.get_registry_meta_data():
            payload.update(artifact_data.get_registry_meta_data())

        url = self.store.registry_artifact_url() + '/{0}/'.format(customer)
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            self.config.logger.info('Artifact registered.')
            return True
        else:
            log_failed_response(self.config, r, 'Unable to register artifact')
            return False

    @staticmethod
    def _get_registry_payload(customer, download_url, sha1, artifact_data):
        return {'name': artifact_data.get_name(),
                'version': artifact_data.get_version(),
                'customer': customer,
                'url': download_url,
                'type': artifact_data.get_type(),
                'checksum': {
                    'sha1': sha1
                }}

    def build(self, project, version, block):
        return self._build_project(project, version, block)

    def _build_project(self, project, version, block):
        if not self._validate_credentials():
            return False

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.id_token)}

        customer = self._get_customer()
        if not customer:
            return False

        payload = self._get_build_payload(customer, project, version)
        builder_url = self.store.builder_url() + '/{0}/'.format(customer) + 'jobs'
        self.config.logger.debug('Queueing build...')
        r = requests.post(builder_url, headers=headers, json=payload)
        if r.status_code == 200:
            hostname = urlparse(self.store.deploy_url()).hostname
            self.config.logger.info('Build queued.')
            self.config.logger.info('You can see the status of your build at '
                                    'https://{}/controller/projects/{}'.format(hostname, project))

            if block:
                job_url = '{}/{}'.format(builder_url, r.json().get('data').get('submittedAt'))

                # 40 minutes approximately since this doesn't account for the request time
                timeout_seconds = 40 * 60
                time_blocked = 0
                while time_blocked < timeout_seconds:
                    r = requests.get(job_url, headers=headers)
                    if not r.status_code == 200:
                        self.config.logger.error('Build status check failed')
                        return False

                    if r.json().get('data').get('status') == 'COMPLETED':
                        self.config.logger.info('Build completed')
                        return True

                    self.config.logger.info('Waiting for build to complete...')
                    time.sleep(20)
                    time_blocked += 20

                self.config.logger.error('Timed out waiting for build to complete.')
                return False

            return True
        else:
            log_failed_response(self.config, r, 'Unable to enqueue build')
            return False

    @staticmethod
    def _get_build_payload(customer, project, version):
        return {'customer': customer,
                'project': project,
                'version': str(version)}

    def deploy(self, item_type, name, version, group, push, no_https):
        if item_type == 'apk':
            return self._deploy_apk(name, version, group, push, no_https)
        elif item_type == 'config':
            return self._deploy_config(name, version, group, push, no_https)
        elif item_type == 'ota':
            return self._deploy_ota(name, version, group, push, no_https)
        else:
            self.config.logger.critical('Unsupported deploy type {}'.format(item_type))
            return False

    def _deploy_apk(self, name, version, group, push, no_https):
        if not self._validate_credentials():
            return False

        customer = self._get_customer()
        if not customer:
            return False

        payload = self._get_deploy_payload(customer, group, name, version, 'apk', push, no_https)
        return self._deploy_payload(payload, 'apk')

    def _deploy_config(self, name, version, group, push, no_https):
        if not self._validate_credentials():
            return False

        customer = self._get_customer()
        if not customer:
            return False

        payload = self._get_deploy_payload(customer, group, name, version, 'config', push, no_https)
        return self._deploy_payload(payload, 'config')

    def _deploy_ota(self, name, version, group, push, no_https):
        if not self._validate_credentials():
            return False

        customer = self._get_customer()
        if not customer:
            return False

        if name != 'mason-os':
            self.config.logger.warning("Unknown name '{0}' for 'ota' deployments. "
                                       "Forcing it to 'mason-os'".format(name))
            name = 'mason-os'
        payload = self._get_deploy_payload(customer, group, name, version, 'ota', push, no_https)
        return self._deploy_payload(payload, 'ota')

    def _deploy_payload(self, payload, type):
        if not payload:
            return False

        if not self.config.skip_verify:
            self.config.logger.info('---------- DEPLOY -----------')

            self.config.logger.info('Name: {}'.format(payload['name']))
            self.config.logger.info('Type: {}'.format(payload['type']))
            self.config.logger.info('Version: {}'.format(payload['version']))
            self.config.logger.info('Group: {}'.format(payload['group']))
            self.config.logger.info('Push: {}'.format(payload['push']))
            self.config.logger.debug('Customer: {}'.format(payload['customer']))

            if payload.get('deployInsecure', False):
                self.config.logger.info()
                self.config.logger.info('***WARNING***')
                self.config.logger.info('--no-https enabled: this deployment will be delivered to '
                                        'devices over HTTP.')
                self.config.logger.info('***WARNING***')

            self.config.logger.info('-----------------------------')

            if not click.confirm('Continue deploy?', default=True):
                return False

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.id_token)}

        r = requests.post(self.store.deploy_url(), headers=headers, json=payload)

        if r.status_code == 200:
            if r.text:
                self.config.logger.debug(r.text)
            self.config.logger.info('{}:{} was successfully deployed to {}'.format(
                payload['name'], payload['version'], payload['group']))
            return True
        else:
            log_failed_response(self.config, r, 'Unable to deploy {}'.format(type))
            return False

    @staticmethod
    def _get_deploy_payload(customer, group, name, version, item_type, push, no_https):
        payload = {
            'customer': customer,
            'group': group,
            'name': name,
            'version': version,
            'type': item_type,
            'push': push
        }
        if no_https:
            payload['deployInsecure'] = no_https
        return payload

    def stage(self, yaml, block):
        if self.register(yaml):
            return self._build_project(self.artifact.get_name(), self.artifact.get_version(), block)
        else:
            self.config.logger.error('Unable to stage configuration')
            return False

    def authenticate(self, user, password):
        payload = self._get_auth_payload(user, password)
        r = requests.post(self.store.auth_url(), json=payload)
        if r.status_code == 200:
            data = r.json()
            return self.persist.write_tokens(data)
        else:
            return False

    def _get_auth_payload(self, user, password):
        return {'client_id': self.store.client_id(),
                'username': user,
                'password': password,
                'id_token': str(self.id_token),
                'connection': 'Username-Password-Authentication',
                'grant_type': 'password',
                'scope': 'openid',
                'device': ''}

    def logout(self):
        return self.persist.delete_tokens()


class UploadInChunks(object):

    def __init__(self, filename, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = int(chunksize)
        self.totalsize = os.stat(filename).st_size
        self.pbar = tqdm(total=self.totalsize, ncols=100, unit='kb', dynamic_ncols=True)

    def __iter__(self):
        with open(self.filename, 'rb') as file_to_upload:
            while True:
                data = file_to_upload.read(self.chunksize)
                if not data:
                    self.pbar.close()
                    break
                self.pbar.update(len(data))
                yield data

    def __len__(self):
        return self.totalsize


class IterableToFileAdapter(object):

    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    def read(self, size=-1):
        return next(self.iterator, b'')

    def __len__(self):
        return self.length
