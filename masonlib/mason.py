import json
import requests
import base64
import os.path
import re
import sys

from lib.apk_parse.apk import APK
from persist import Persist
from utils import Utils
from store import Store
from progressbar import ProgressBar

class Mason(object):
    def __init__(self, config):
        self.config = config
        self.id_token = None
        self.access_token = None
        self.apkf = None
        self.persist = Persist('.masonrc')
        self.store = Store(os.path.join(os.path.expanduser('~'), '.mason.yml'))

    # public parse method, returns true if supported artifact, false otherwise
    def parse(self, artifact):
        if not os.path.isfile(artifact):
            print 'No file provided'
            return False

        apkf = APK(artifact)

        # Bail on non valid apk
        if not apkf.is_valid_APK():
            print "Not a valid APK, only APK's are currently supported"
            return False

        # Check for 'Android Debug' CN for the given artifact, disallow upload
        #for line in apkf.cert_text.splitlines():
        #    if re.search('Subject:', line):
        #        if re.search('Android Debug', line):
        #            print '\n------------------WARNING------------------\n' \
        #                  'Not allowing android debug key signed apk. \n' \
        #                  'Please sign the APK with your release keys \n' \
        #                  'before attempting to upload.               \n' \
        #                  '------------------WARNING------------------\n'
        #            return False

        print '------------ APK ------------'
        print 'File Name: ' + apkf.filename
        print 'File size: ', apkf.file_size
        print 'Package: ' + apkf.package
        print 'Version Name: ' + apkf.get_androidversion_name()
        print 'Version Code: ' + apkf.get_androidversion_code()
        #if self.config.verbose:
        #    print 'Cert md5: ' + apkf.cert_md5
        #    print apkf.cert_text
        print '-----------------------------'
        self.apkf = apkf
        return True

    # public publish method, returns true if published, false otherwise
    def publish(self, artifact):
        self.id_token = self.persist.retrieve_id_token()
        self.access_token = self.persist.retrieve_access_token()

        if not self.id_token or not self.access_token:
            return False

        sha1 = Utils.hash_file(artifact, 'sha1', True)
        if self.config.verbose:
            print 'File SHA1: ' + sha1
        md5 = Utils.hash_file(artifact, 'md5', False)
        if self.config.verbose:
            print 'File MD5: ' + Utils.hash_file(artifact, 'md5', True)

        # Get the user info
        user_info_data = self.__request_user_info()

        if not user_info_data:
            return False

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]

        # Get the signed url data for the user and artifact
        signed_url_data = self.__request_signed_url(customer, self.apkf, md5)

        if not signed_url_data:
            return False

        # Get the signed request url from the response
        signed_request_url = signed_url_data['signed_request']

        # Store the download url for mason registry
        download_url = signed_url_data['url']

        # Upload the artifact to the signed url
        if not self.__upload_to_signed_url(signed_request_url, artifact, md5):
            return False

        # Publish to mason services
        if not self.__register_to_mason(customer, download_url, sha1, self.apkf):
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

    def __request_signed_url(self, customer, apkf, md5):
        print 'Connecting to server...'
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        headers = {'Content-Type': 'application/json',
                   'Content-MD5': base64encodedmd5,
                   'Authorization': 'Bearer ' + self.id_token}
        url = self.store.registry_signer_url() + '/{0}/{1}/{2}'.format(customer, apkf.package, apkf.get_androidversion_name())
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            data = json.loads(r.text)
            return data
        else:
            print 'Unable to get signed url ', r.status_code
            return None

    def __upload_to_signed_url(self, url, artifact, md5):
        print 'Uploading artifact...'
        base64encodedmd5 = base64.b64encode(md5).decode('utf-8')
        headers = {'Content-Type': 'application/vnd.android.package-archive',
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

    def __register_to_mason(self, customer, download_url, sha1, apkf):
        print 'Registering to mason services...'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.id_token}
        payload = {'name': apkf.package,
                   'version': apkf.get_androidversion_name(),
                   'customer': customer,
                   'apk': {
                       'versionCode': apkf.get_androidversion_code(),
                       'packageName': apkf.package
                   },
                   'url': download_url,
                   'checksum': {
                       'sha1': sha1
                   }}
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

class upload_in_chunks(object):
    def __init__(self, filename, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(filename)
        self.readsofar = 0
        self.pbar = ProgressBar(maxval=self.totalsize)

    def __iter__(self):
        self.pbar.start()
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    sys.stderr.write("\n")
                    self.pbar.finish()
                    break
                self.readsofar += len(data)
                self.pbar.update(self.readsofar)
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

