import json
import requests
import base64
import os.path

from apk import Apk
from media import Media
from os_config import OSConfig
from persist import Persist
from utils import Utils
from store import Store
from tqdm import tqdm

class Mason(object):
    """ The main Mason interface. Provides methods that allow you to parse, register, build, and deploy artifacts.

        :param config: A global config object detailing verbosity and extra functions."""

    def __init__(self, config):
        self.config = config
        self.id_token = None
        self.access_token = None
        self.artifact = None
        self.persist = Persist('.masonrc')
        self.store = Store(os.path.join(os.path.expanduser('~'), '.mason.yml'))

    def parse_apk(self, apk):
        """ Public apk parse method, returns true if supported artifact, false otherwise

            :param apk: specify the path of the apk file
            :rtype: boolean"""
        apk = Apk.parse(self.config, apk)

        if not apk:
            return False

        self.artifact = apk
        return True

    def parse_media(self, name, type, version, binary):
        """ Public media parse method, returns true if supported artifact, false otherwise

            :param name: specify the name of the media artifact
            :param type: specify the type of the media artifact
            :param version: specify the unique version of the media artifact
            :param binary: specify the path of the media binary file
            :rtype: boolean"""
        media = Media.parse(self.config, name, type, version, binary)

        if not media:
            return False

        self.artifact = media
        return True

    def parse_os_config(self, config_yaml):
        """ Public os parse method, returns true if supported artifact, false otherwise

            :param config_yaml: specify the path of the os configuration yaml file
            :rtype: boolean"""
        os_config = OSConfig.parse(self.config, config_yaml)

        if not os_config:
            return False

        self.artifact = os_config
        return True

    def register(self, binary):
        """ Register a given binary. Need to call one of the parse commands prior to invoking register to validate
            a given artifact and decorate it with the necessary metadata for service upload.

            :param binary: specify the path of the artifact file"""
        if not self.config.skip_verify:
            response = raw_input('Continue register? (y)')
            if not response or response == 'y':
                if not self.__register_artifact(binary):
                    exit('Unable to register artifact')
            else:
                exit('Artifact register aborted')
        else:
            if not self.__register_artifact(binary):
                exit('Unable to register artifact')

    def __register_artifact(self, binary):
        self.id_token = self.persist.retrieve_id_token()
        self.access_token = self.persist.retrieve_access_token()

        if not self.id_token or not self.access_token:
            print 'Please run \'mason login\' first'
            return False

        sha1 = Utils.hash_file(binary, 'sha1', True)
        if self.config.verbose:
            print 'File SHA1: ' + sha1
        md5 = Utils.hash_file(binary, 'md5', False)
        if self.config.verbose:
            print 'File MD5: ' + Utils.hash_file(binary, 'md5', True)

        # Get the user info
        user_info_data = self.__request_user_info()

        if not user_info_data:
            return False

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]

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
        print 'Requesting user info...'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        r = requests.get(self.store.user_info_url(), headers=headers)

        if r.status_code == 200:
            data = json.loads(r.text)
            return data
        else:
            print 'Unable to get user info: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            return None

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
        if status_code == 401:
            print 'User token is expired or user is unauthorized'
        elif status_code == 403:
            print 'Access to domain is forbidden. Please contact support.'

    def build(self, project, version):
        """ Public bulid method, returns true if build started, false otherwise

            :param project: specify the name of the project to start a build for
            :param version: specify the version of the project for which to start a build for
            :rtype: boolean"""
        return self.__build_project(project, version)

    def __build_project(self, project, version):
        self.id_token = self.persist.retrieve_id_token()
        self.access_token = self.persist.retrieve_access_token()

        if not self.id_token or not self.access_token:
            print 'Please run \'mason login\' first'
            return False

        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + str(self.id_token)}

        # Get the user info
        user_info_data = self.__request_user_info()

        if not user_info_data:
            return False

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]

        payload = self.__get_build_payload(customer, project, version)
        builder_url = self.store.builder_url() + '/{0}/'.format(customer) + 'jobs'
        print 'Starting build...'
        r = requests.post(builder_url, headers=headers, json=payload)
        if r.status_code == 200:
            data = json.loads(r.text)
            job_id = data['jobId']
            print 'Started build: ' + job_id
            return True
        else:
            print 'Unable to enqueue build: ' + str(r.status_code)
            self.__handle_status(r.status_code)
            return False

    def __get_build_payload(self, customer, project, version):
        return {'customer': customer,
                'project': project,
                'version': str(version)}

    def authenticate(self, user, password):
        """ Public authentication method, returns true if authed, false otherwise

            :param user: specify a user as string
            :param password: specify a password as string
            :rtype: boolean"""
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
        """ Public logout method, returns true if successfully logged out
            :rtype: boolean"""
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