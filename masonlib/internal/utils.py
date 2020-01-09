import hashlib

import click
import requests

from masonlib.internal.store import Store

LOG_PROTOCOL_TRACE = 4

AUTH = Store('auth', {
    'api_key': None,
    'id_token': None,
    'access_token': None
})
ENDPOINTS = Store('endpoints', {
    'client_id': 'QLWpUwYOOcLlAJsmyQhQMXyeWn6RZpoc',
    'auth_url': 'https://bymason.auth0.com/oauth/ro',
    'user_info_url': 'https://bymason.auth0.com/userinfo',
    'registry_artifact_url': 'https://platform.bymason.com/api/registry/artifacts',
    'registry_signed_url': 'https://platform.bymason.com/api/registry/signedurl',
    'builder_url': 'https://platform.bymason.com/api/tracker/builder',
    'deploy_url': 'https://platform.bymason.com/api/deploy',
    'xray_url': 'wss://api.bymason.com/v1/global/xray',
    'config_version': 1
})


def validate_credentials(config):
    if not AUTH['id_token'] or not AUTH['access_token']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_version(config, version, type):
    try:
        version = int(version)
    except ValueError:
        config.logger.error("Error in {}: '{}' is not a number.".format(type, version))
        raise click.Abort()

    if not (0 < version < 2147483647):
        config.logger.error('The {} version cannot be negative or larger '
                            'than MAX_INT (2147483647).'.format(type))
        raise click.Abort()


def hash_file(filename, type_of_hash, as_hex):
    """
    Hash a file using SHA1 or MD5
    :param filename:
    :param type_of_hash: 'sha1' or 'md5'
    :param as_hex: True to return a string of hex digits
    :return: The hash of the requested file
    """

    if type_of_hash == 'sha1':
        h = hashlib.sha1()
    else:
        h = hashlib.md5()

    with open(filename, 'rb') as file_to_hash:
        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file_to_hash.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    if as_hex:
        return h.hexdigest()
    else:
        # return regular digest
        return h.digest()


def safe_request(config, type, *args, **kwargs):
    func = getattr(requests, type)
    try:
        return func(*args, **kwargs)
    except requests.RequestException as e:
        config.logger.debug('{} request to {} failed: {}'.format(type.upper(), args[0], e))
        config.logger.error('Network request failed. Check you internet connection.')
        raise click.Abort()


def handle_failed_response(config, r, message):
    config.logger.debug('{}: {}'.format(message, r.status_code))
    _handle_status(config, r.status_code)

    if r.text:
        _handle_errors_new_type(config, r)
        _handle_errors_old_type(config, r)
        config.logger.error(r.text)

    raise click.Abort()


def _handle_status(config, status_code):
    if status_code == 400:
        config.logger.debug('Client made a bad request, failed.')
    elif status_code == 401:
        config.logger.error("Unauthorized: session expired or access denied. Run 'mason login' to "
                            "start a new session.")
        raise click.Abort()
    elif status_code == 403:
        config.logger.error('Access to domain is forbidden. Please contact support.')
    elif status_code == 404:
        config.logger.debug('Resource is unavailable, failed')
    elif status_code == 500:
        config.logger.debug('Mason service or resource is currently unavailable.')


def _handle_errors_new_type(config, r):
    """
    Makes an effort to parse body of the `response` object as JSON, and if so, looks for the
    following standard field schema:
    ::

        {
            'error': 'error name',
            'details' : 'description of error',
            'itemized' : [
                {
                    'code': 'xxx',
                    'message': 'specifics'
                },..
            ]
        }

    If JSON is not detected, just prints `body` as text. Colorizes in red if the option is set in
    `config`.

    :param config: Global config object
    :param r: Response
    """

    try:
        err_result = r.json()
        config.logger.debug(err_result)

        if 'itemized' in err_result:
            for item in err_result['itemized']:
                if item['code'] == '8f92ccpl':
                    config.logger.error(item['message'])
                    config.logger.info(
                        'Create a new project: https://platform.bymason.com/controller/projects')
                    raise click.Abort()
                else:
                    config.logger.error("{} (code: '{}')".format(item['message'], item['code']))

        details = err_result['details']
        if type(details) is list:
            details = [detail['message'] for detail in details]
        config.logger.error('{}: {}'.format(err_result['error'], details))
    except (KeyError, ValueError):
        return

    raise click.Abort()


def _handle_errors_old_type(config, r):
    try:
        details = r.json()['error']['details']
        config.logger.error(details)
    except (KeyError, ValueError):
        try:
            config.logger.error(r.json()['data'])
        except (KeyError, ValueError):
            try:
                config.logger.error(r.json()['message'])
            except (KeyError, ValueError):
                return

    raise click.Abort()
