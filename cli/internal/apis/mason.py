import base64
from threading import Lock

from rfc3339 import parse_datetime

from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError


class MasonApi:
    def __init__(self, handler, auth_store, endpoints_store):
        self.handler = handler
        self.auth_store = auth_store
        self.endpoints_store = endpoints_store

        self.lock = Lock()
        self._customer = None

    def get_projects(self):
        customer = self._get_validated_customer()
        return self._get_projects(customer)

    def upload_artifact(self, binary, artifact):
        customer = self._get_validated_customer()
        signed_url = self._get_signed_url(customer, binary, artifact)
        upload_url = signed_url['signed_request']
        download_url = signed_url['url']

        self._upload_to_signed_url(upload_url, binary, artifact)
        return self._register_signed_url(customer, download_url, binary, artifact)

    def deploy_artifact(self, type, name, version, group, push, no_https):
        customer = self._get_validated_customer()
        return self._deploy_artifact(customer, type, name, version, group, push, no_https)

    def get_latest_artifact(self, name, type):
        def sort(artifact):
            return parse_datetime(artifact.get('createdAt')).timestamp()

        customer = self._get_validated_customer()
        return self._find_artifact(customer, name, type, sort)

    def get_highest_artifact(self, name, type):
        def sort(artifact):
            return int(artifact.get('version'))

        customer = self._get_validated_customer()
        return self._find_artifact(customer, name, type, sort)

    def start_build(self, project, version, fast_build, mason_version):
        customer = self._get_validated_customer()
        return self._start_build(customer, project, version, fast_build, mason_version)

    def get_build(self, id):
        customer = self._get_validated_customer()
        return self._get_build(customer, id)

    def login(self, username, password):
        return self._login(password, username)

    def _get_projects(self, customer):
        headers = {
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['projects_url'] + '/{}'.format(customer)
        return self.handler.get(url, headers=headers)

    def _get_signed_url(self, customer, binary, artifact):
        md5 = hash_file(binary, 'md5', False)
        headers = {
            'Content-Type': 'application/json',
            'Content-MD5': base64.b64encode(md5).decode('utf-8'),
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['registry_signed_url'] + '/{0}/{1}/{2}?type={3}'.format(
            customer, artifact.get_name(), artifact.get_version(), artifact.get_type())
        return self.handler.get(url, headers=headers)

    def _upload_to_signed_url(self, signed_url, binary, artifact):
        md5 = hash_file(binary, 'md5', False)
        headers = {
            'Content-Type': artifact.get_content_type(),
            'Content-MD5': base64.b64encode(md5).decode('utf-8')
        }

        self.handler.put(signed_url, binary, headers=headers)

    def _register_signed_url(self, customer, signed_url, binary, artifact):
        sha1 = hash_file(binary, 'sha1')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }
        payload = {
            'name': str(artifact.get_name()),
            'version': str(artifact.get_version()),
            'customer': customer,
            'url': signed_url,
            'type': str(artifact.get_type()),
            'checksum': {
                'sha1': sha1
            }
        }

        if artifact.get_registry_meta_data():
            payload.update(artifact.get_registry_meta_data())

        url = self.endpoints_store['registry_artifact_url'] + '/{0}'.format(customer)
        self.handler.post(url, headers=headers, json=payload)

    def _deploy_artifact(self, customer, type, name, version, group, push, no_https):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }
        payload = {
            'customer': customer,
            'group': str(group),
            'name': str(name),
            'version': str(version),
            'type': str(type),
            'push': bool(push),
            'deployInsecure': bool(no_https)
        }

        url = self.endpoints_store['deploy_url']
        self.handler.post(url, headers=headers, json=payload)

    def _get_artifact(self, customer, name, type_, version):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['registry_artifact_url'] + '/{}/{}/{}/{}'.format(
            customer, type_, name, version)
        return self.handler.get(url, headers=headers)

    def _find_artifact(self, customer, name, type_, sort):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['registry_artifact_url'] + '/{}/{}/{}'.format(
            customer, type_, name)
        result = self.handler.get(url, headers=headers)

        if not type(result) == list:
            return None

        sorted_artifacts = sorted(result, key=sort, reverse=True)
        for artifact in sorted_artifacts:
            if artifact.get('name') == name and artifact.get('type') == type_:
                return self._get_artifact(customer, name, type_, artifact.get('version'))

    def _start_build(self, customer, project, version, fast_build, mason_version):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }
        payload = {
            'customer': customer,
            'project': str(project),
            'version': str(version),
            'fastBuild': bool(fast_build),
        }
        if mason_version:
            payload['masonVersion'] = str(mason_version)

        url = self.endpoints_store['builder_url'] + '/{0}/jobs'.format(customer)
        return self.handler.post(url, headers=headers, json=payload)

    def _get_build(self, customer, id):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['builder_url'] + '/{}/jobs/{}'.format(customer, id)
        return self.handler.get(url, headers=headers)

    def _login(self, password, username):
        payload = {
            'client_id': self.endpoints_store['client_id'],
            'username': username,
            'password': password,
            'id_token': str(self.auth_store['id_token']),
            'connection': 'Username-Password-Authentication',
            'grant_type': 'password',
            'scope': 'openid',
            'device': ''
        }
        url = self.endpoints_store['auth_url']
        return self.handler.post(url, json=payload)

    def _get_validated_customer(self):
        with self.lock:
            return self._safe_get_validated_customer()

    def _safe_get_validated_customer(self):
        if self._customer:
            return self._customer

        # Get the user info
        headers = {'Authorization': 'Bearer {}'.format(self.auth_store['access_token'])}
        user_info_data = self.handler.get(
            self.endpoints_store['user_info_url'], headers=headers)
        if not user_info_data:
            raise ApiError('Customer info not found.')

        # Extract the customer info
        customer = user_info_data['user_metadata']['clients'][0]
        if not customer:
            raise ApiError('Could not retrieve customer information.')
        self._customer = customer

        return customer
