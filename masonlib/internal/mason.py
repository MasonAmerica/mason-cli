import base64
import json
import os.path
import requests

from tqdm import tqdm
from urlparse import urlparse

from masonlib.imason import IMason
from masonlib.internal.apk import Apk
from masonlib.internal.media import Media
from masonlib.internal.os_config import OSConfig
from masonlib.internal.persist import Persist
from masonlib.internal.store import Store
from masonlib.internal.utils import Utils

class Mason(IMason):

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

    def __validate_credentials(self):
        self.id_token = self.persist.retrieve_id_token()
        self.access_token = self.persist.retrieve_access_token()

        if not self.id_token or not self.access_token:
            print 'Please run \'mason login\' first'
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
            response = raw_input('Continue register? (y)')
            if not response or response == 'y':
                if not self.__register_artifact(binary):
                    print 'Unable to register artifact'
                    return False
                else:
                    return True
            else:
                print 'Artifact register aborted'
                return False
        else:
            if not self.__register_artifact(binary):
                print 'Unable to register artifact'
                return False
            else:
                return True

    def __register_artifact(self, binary):
        if not self.__validate_credentials():
            return False

        sha1 = Utils.hash_file(binary, 'sha1', True)
        if self.config.verbose:
            print 'File SHA1: ' + sha1
        md5 = Utils.hash_file(binary, 'md5', False)
        if self.config.verbose:
            print 'File MD5: ' + Utils.hash_file(binary, 'md5', True)

        customer = self.__get_customer()
        if not customer:
            print 'Could not retrieve customer information'
            return False

        # Get the signed url data for the user and artifact
        signed_url_data = self.__request_signed_url(customer, self.artifact, md5)

        if not signed_url_data:
            return False

        # Get the signed request url from the response
        signed_request_url = signed_url_data['signed_request']

        # Store the download url for mason registry
        download_url = signed_url_data['url']

        # Upload the artifact to the signed url
        if not self.__upload_to_signed_url(signed_request_url, binary, self.artifact, md5):
            return False

        # Publish to mason services
        if not self.__register_to_mason(customer, download_url, sha1, self.artifact):
            return False

        return True

    def __request_user_info(self):
        headers = {'Authorization': 'Bearer ' + self.access_token}
        r = requests.get(self.store.user_info_url(), headers=headers)

        if r.status_code == 200:
            data = json.loads(r.text)
            return data
        else:
            print 'Unable to get user info: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return None

    def __get_customer(self):
        # Get the user info
        user_info_data = self.__request_user_info()

        if not user_info_data:
            return None

        # Extract the customer info
        return user_info_data['user_metadata']['clients'][0]

    def __request_signed_url(self, customer, artifact_data, md5):
        print 'Connecting to server...'
        headers = self.__get_signed_url_request_headers(md5)
        url = self.__get_signed_url_request_endpoint(customer, artifact_data)
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = json.loads(r.text)
            return data
        else:
            print 'Unable to get signed url: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return None

    def __get_signed_url_request_headers(self, md5):
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        return {'Content-Type': 'application/json',
                'Content-MD5': base64encodedmd5,
                'Authorization': 'Bearer ' + str(self.id_token)}

    def __get_signed_url_request_endpoint(self, customer, artifact_data):
        return self.store.registry_signer_url() \
              + '/{0}/{1}/{2}'.format(customer, artifact_data.get_name(), artifact_data.get_version()) \
              + '?type=' + artifact_data.get_type()

    def __upload_to_signed_url(self, url, artifact, artifact_data, md5):
        print 'Uploading artifact...'
        headers = self.__get_signed_url_post_headers(artifact_data, md5)
        file = open(artifact, 'rb')
        iterable = upload_in_chunks(file.name, chunksize=10)

        r = requests.put(url, data=IterableToFileAdapter(iterable), headers=headers)
        if r.status_code == 200:
            print 'File upload complete.'
            return True
        else:
            print 'Unable to upload to signed url: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return False

    def __get_signed_url_post_headers(self, artifact_data, md5):
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        return {'Content-Type': artifact_data.get_content_type(),
                'Content-MD5': base64encodedmd5}

    def __register_to_mason(self, customer, download_url, sha1, artifact_data):
        print 'Registering to mason services...'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + str(self.id_token)}
        payload = self.__get_registry_payload(customer, download_url, sha1, artifact_data)

        if artifact_data.get_registry_meta_data():
            payload.update(artifact_data.get_registry_meta_data())

        url = self.store.registry_artifact_url() + '/{0}/'.format(customer)
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print 'Artifact registered.'
            return True
        else:
            print 'Unable to register artifact: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return False

    def __get_registry_payload(self, customer, download_url, sha1, artifact_data):
        return {'name': artifact_data.get_name(),
                   'version': artifact_data.get_version(),
                   'customer': customer,
                   'url': download_url,
                   'type': artifact_data.get_type(),
                   'checksum': {
                       'sha1': sha1
                   }}

    def __handle_status(self, status_code):
        if status_code == 400:
            print 'Client made a bad request, failed.'
        elif status_code == 401:
            print 'User token is expired or user is unauthorized.'
        elif status_code == 403:
            print 'Access to domain is forbidden. Please contact support.'
        elif status_code == 404:
            print 'Resource is unavailable, failed'
        elif status_code == 500:
            print 'Mason service or resource is currently unavailable.'

    def build(self, project, version):
        return self.__build_project(project, version)

    def __build_project(self, project, version):
        if not self.__validate_credentials():
            return False

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + str(self.id_token)}

        customer = self.__get_customer()
        if not customer:
            print 'Could not retrieve customer information'
            return False

        payload = self.__get_build_payload(customer, project, version)
        builder_url = self.store.builder_url() + '/{0}/'.format(customer) + 'jobs'
        print 'Queueing build...'
        r = requests.post(builder_url, headers=headers, json=payload)
        if r.status_code == 200:
            hostname = urlparse(self.store.deploy_url()).hostname
            print 'Build queued.\nYou can see the status of your build at https://{}/builds'.format(hostname)
            return True
        else:
            print 'Unable to enqueue build: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return False

    def __get_build_payload(self, customer, project, version):
        return {'customer': customer,
                'project': project,
                'version': str(version)}

    def deploy(self, item_type, name, version, group, push):
        if item_type == 'apk':
            return self.__deploy_apk(name, version, group, push)
        elif item_type == 'config':
            return self.__deploy_config(name, version, group, push)
        else:
            print 'Unsupported deploy type ' + str(item_type)
            return False

    def __deploy_apk(self, name, version, group, push):
        if not self.__validate_credentials():
            return False

        customer = self.__get_customer()
        if not customer:
            print 'Could not retrieve customer information'
            return False

        payload = self.__get_deploy_payload(customer, group, name, version, 'apk', push)
        return self.__deploy_payload(payload)

    def __deploy_config(self, name, version, group, push):
        if not self.__validate_credentials():
            return False

        customer = self.__get_customer()
        if not customer:
            print 'Could not retrieve customer information'
            return False

        payload = self.__get_deploy_payload(customer, group, name, version, 'config', push)
        return self.__deploy_payload(payload)

    def __deploy_payload(self, payload):
        if not payload:
            return False

        if not self.config.skip_verify:
            print '---------- DEPLOY -----------'
            print 'Name: ' + str(payload['name'])
            print 'Type: ' + str(payload['type'])
            print 'Version: ' + str(payload['version'])
            print 'Group: ' + str(payload['group'])
            print 'Push: ' + str(payload['push'])
            if self.config.verbose:
                print 'Customer: ' + str(payload['customer'])
            print '-----------------------------'
            response = raw_input('Continue deploy? (y)')
            if not response or response == 'y':
                print 'Continuing deploy...'
            else:
                print 'Deploy aborted'
                return False

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + str(self.id_token)}

        r = requests.post(self.store.deploy_url(), headers=headers, json=payload)

        if r.status_code == 200:
            if r.text:
                if self.config.verbose:
                    print r.text
            print str(payload['name']) + ':' + str(payload['version']) \
                  + ' was succesfully deployed to ' + str(payload['group'])
            return True
        else:
            self.__handle_status(r.status_code)
            if r.text:
                if self.config.debug:
                    print r.text
            return False

    def __get_deploy_payload(self, customer, group, name, version, item_type, push):
        return {
            'customer': customer,
            'group': group,
            'name': name,
            'version': version,
            'type': item_type,
            'push': push
        }

    def stage(self, yaml):
        if self.register(yaml):
            return self.__build_project(self.artifact.get_name(), self.artifact.get_version())
        else:
            print 'Unable to stage configuration'
            return False

    def authenticate(self, user, password):
        payload = self.__get_auth_payload(user, password)
        r = requests.post(self.store.auth_url(), json=payload)
        if r.status_code == 200:
            data = json.loads(r.text)
            return self.persist.write_tokens(data)
        else:
            return False

    def __get_auth_payload(self, user, password):
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

class upload_in_chunks(object):
    def __init__(self, filename, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(filename)
        self.pbar = tqdm(total=self.totalsize, ncols=100, unit='kb', dynamic_ncols=True, unit_scale='kb')

    def __iter__(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
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