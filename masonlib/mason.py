import json
import requests
import base64
import os.path
import sys

from apk import Apk
from media import Media
from os_config import OSConfig
from persist import Persist
from utils import Utils
from store import Store
from tqdm import tqdm

class Mason(object):
    def __init__(self, config):
        self.config = config
        self.id_token = None
        self.access_token = None
        self.artifact = None
        self.persist = Persist('.masonrc')
        self.store = Store(os.path.join(os.path.expanduser('~'), '.mason.yml'))

    # public apk parse method, returns true if supported artifact, false otherwise
    def parse_apk(self, apk):
        apk = Apk.parse(self.config, apk)

        if not apk:
            return False

        self.artifact = apk
        return True

    # public media parse method, returns true if supported artifact, false otherwise
    def parse_media(self, name, type, version, binary):
        media = Media.parse(self.config, name, type, version, binary)

        if not media:
            return False

        self.artifact = media
        return True

    # public os parse method, returns true if supported artifact, false otherwise
    def parse_os_config(self, config_yaml):
        os_config = OSConfig.parse(self.config, config_yaml)

        if not os_config:
            return False

        self.artifact = os_config
        return True

    # public register method
    def register(self, binary):
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
            print 'Unable to get user info ', r.status_code
            return None

    def __request_signed_url(self, customer, artifact_data, md5):
        print 'Connecting to server...'
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        headers = {'Content-Type': 'application/json',
                   'Content-MD5': base64encodedmd5,
                   'Authorization': 'Bearer ' + self.id_token}
        url = self.store.registry_signer_url() \
              + '/{0}/{1}/{2}'.format(customer, artifact_data.get_name(), artifact_data.get_version()) \
              + '?type=' + artifact_data.get_type()

        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = json.loads(r.text)
            return data
        else:
            print 'Unable to get signed url ', r.status_code
            return None

    def __upload_to_signed_url(self, url, artifact, artifact_data, md5):
        print 'Uploading artifact...'
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        headers = {'Content-Type': artifact_data.get_content_type(),
                       'Content-MD5': base64encodedmd5}
        file = open(artifact, 'rb')
        iterable = upload_in_chunks(file.name, chunksize=10)

        r = requests.put(url, data=IterableToFileAdapter(iterable), headers=headers)
        if r.status_code == 200:
            print 'File upload complete.'
            return True
        else:
            print 'Unable to upload to signed url: ', r.status_code
            print r.text
            return False

    def __register_to_mason(self, customer, download_url, sha1, artifact_data):
        print 'Registering to mason services...'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.id_token}
        payload = {'name': artifact_data.get_name(),
                   'version': artifact_data.get_version(),
                   'customer': customer,
                   'url': download_url,
                   'type': artifact_data.get_type(),
                   'checksum': {
                       'sha1': sha1
                   }}

        if artifact_data.get_registry_meta_data():
            payload.update(artifact_data.get_registry_meta_data())

        url = self.store.registry_artifact_url() + '/{0}/'.format(customer)
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print 'Artifact registered.'
            return True
        else:
            print 'Unable to register artifact. ', r.status_code
            return False

    # public auth method, returns true if authed, false otherwise
    def authenticate(self, user, password):
        payload = {'client_id': self.store.client_id(),
                   'username': user,
                   'password': password,
                   'id_token': self.id_token,
                   'connection': 'Username-Password-Authentication',
                   'grant_type': 'password',
                   'scope': 'openid',
                   'device': ''}

        r = requests.post(self.store.auth_url(), json=payload)

        if r.status_code == 200:
            data = json.loads(r.text)
            return self.persist.write_tokens(data)
        else:
            return False

    # public logout method, returns true if successfully logged out
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