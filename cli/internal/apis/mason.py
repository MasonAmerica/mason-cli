import base64

from cli.internal.utils.hashing import hash_file
from cli.internal.utils.remote import ApiError


class MasonApi:
    def __init__(self, handler, auth_store, endpoints_store):
        self.handler = handler
        self.auth_store = auth_store
        self.endpoints_store = endpoints_store

        self._customer = None

    def upload_artifact(self, binary, artifact):
        customer = self._get_validated_customer()
        signed_url = self._get_signed_url(customer, binary, artifact)
        upload_url = signed_url['signed_request']
        download_url = signed_url['url']

        self._upload_to_signed_url(upload_url, binary, artifact)
        self._register_signed_url(customer, download_url, binary, artifact)

    def deploy_artifact(self, type, name, version, group, push, no_https):
        customer = self._get_validated_customer()
        self._deploy_artifact(customer, type, name, version, group, push, no_https)

    def start_build(self, project, version, fast_build):
        customer = self._get_validated_customer()
        return self._start_build(customer, project, version, fast_build)

    def get_build(self, id):
        customer = self._get_validated_customer()
        return self._get_build(customer, id)

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
        sha1 = hash_file(binary, 'sha1', True)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }
        payload = {
            'name': artifact.get_name(),
            'version': artifact.get_version(),
            'customer': customer,
            'url': signed_url,
            'type': artifact.get_type(),
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
            'group': group,
            'name': name,
            'version': str(version),
            'type': type,
            'push': push
        }
        if no_https:
            payload['deployInsecure'] = no_https

        url = self.endpoints_store['deploy_url']
        self.handler.post(url, headers=headers, json=payload)

    def _start_build(self, customer, project, version, fast_build):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }
        payload = {
            'customer': customer,
            'project': project,
            'version': str(version)
        }
        if fast_build:
            payload['fastBuild'] = fast_build

        url = self.endpoints_store['builder_url'] + '/{0}/jobs'.format(customer)
        return self.handler.post(url, headers=headers, json=payload)

    def _get_build(self, customer, id):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.auth_store['id_token'])
        }

        url = self.endpoints_store['builder_url'] + '/{}/jobs/{}'.format(customer, id)
        return self.handler.get(url, headers=headers)

    def _get_validated_customer(self):
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
