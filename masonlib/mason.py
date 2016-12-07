import json
import requests
import base64
import os.path
import re
import sys

from lib.apk_parse.apk import APK
from artifacts import Media
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
        self.media = None
        self.persist = Persist('.masonrc')
        self.store = Store(os.path.join(os.path.expanduser('~'), '.mason.yml'))

    # public parse method, returns true if supported artifact, false otherwise
    def parse_apk(self, apk):
        if not os.path.isfile(apk):
            print 'No file provided'
            return False

        apkf = APK(apk)

        # Bail on non valid apk
        if not apkf.is_valid_APK():
            print "Not a valid APK, only APK's are currently supported"
            return False

        # Check for 'Android Debug' CN for the given artifact, disallow upload
        for line in apkf.cert_text:
            if re.search('Subject:', line):
                if re.search('Android Debug', line):
                    print '\n------------------WARNING------------------\n' \
                          'Not allowing android debug key signed apk. \n' \
                          'Please sign the APK with your release keys \n' \
                          'before attempting to upload.               \n' \
                          '------------------WARNING------------------\n'
                    return False

        print '------------ APK ------------'
        print 'File Name: ' + apkf.filename
        print 'File size: ', str(os.path.getsize(apk))
        print 'Package: ' + apkf.package
        print 'Version Name: ' + apkf.get_androidversion_name()
        print 'Version Code: ' + apkf.get_androidversion_code()
        if self.config.verbose:
            for line in apkf.cert_text:
                print line
        print '-----------------------------'
        self.apkf = apkf
        return True

    def parse_media(self, name, type, version, binary):
        if not os.path.isfile(binary):
            print 'No file provided'
            return False

        media = Media(name, type, version, binary)

        # Bail on non valid apk
        if not media.is_valid_media():
            print "Not a valid " + type + ", see type requirements in the documentation"
            return False

        print '----------- MEDIA -----------'
        print 'File Name: ' + media.binary
        print 'File size: ' + str(os.path.getsize(binary))
        print 'Name: ' + media.name
        print 'Version: ' + media.version
        print 'Type: ' + media.type
        if self.config.verbose:
            if media.details:
                print 'Details: '
                lines = list(line for line in (l.strip() for l in media.details) if line)
                for line in lines:
                    print line
        print '-----------------------------'
        self.media = media
        return True

    # public register apk method, returns true if published, false otherwise
    def register_apk(self, apk):
        return self.__register_artifact(apk, self.apkf)

    # public register media method, returns true if published, false otherwise
    def register_media(self, binary):
        return self.__register_artifact(binary, self.media)

    def __register_artifact(self, binary, artifact_data):
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
        signed_url_data = self.__request_signed_url(customer, artifact_data, md5)

        if not signed_url_data:
            return False

        # Get the signed request url from the response
        signed_request_url = signed_url_data['signed_request']

        # Store the download url for mason registry
        download_url = signed_url_data['url']

        # Upload the artifact to the signed url
        if not self.__upload_to_signed_url(signed_request_url, binary, artifact_data, md5):
            return False

        # Publish to mason services
        if not self.__register_to_mason(customer, download_url, sha1, artifact_data):
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
        if isinstance(artifact_data, APK):
            url = self.store.registry_signer_url() + '/{0}/{1}/{2}'.format(customer, artifact_data.package,
                                                                           artifact_data.get_androidversion_name())
        elif isinstance(artifact_data, Media):
            url = self.store.registry_signer_url() + '/{0}/{1}/{2}?type=media'.format(customer, artifact_data.name,
                                                                           artifact_data.version)
        else:
            print 'Unsupported artifact type'
            return None

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
        if isinstance(artifact_data, APK):
            headers = {'Content-Type': 'application/vnd.android.package-archive',
                       'Content-MD5': base64encodedmd5}
        elif isinstance(artifact_data, Media):
            if artifact_data.type == 'bootanimation':
                headers = {'Content-Type': 'application/zip',
                           'Content-MD5': base64encodedmd5}
            else:
                print 'Unsupported media type'
                return None
        else:
            print 'Unsupported artifact type'
            return None

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
        if isinstance(artifact_data, APK):
            payload = {'name': artifact_data.package,
                       'version': artifact_data.get_androidversion_name(),
                       'customer': customer,
                       'apk': {
                           'versionCode': artifact_data.get_androidversion_code(),
                           'packageName': artifact_data.package
                       },
                       'url': download_url,
                       'checksum': {
                           'sha1': sha1
                       }}
        elif isinstance(artifact_data, Media):
            payload = {'name': artifact_data.name,
                       'version': artifact_data.version,
                       'customer': customer,
                       'media': {
                           'type': artifact_data.type,
                       },
                       'url': download_url,
                       'checksum': {
                           'sha1': sha1
                       }}
        else:
            print 'Unsupported artifact type'
            return None

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

