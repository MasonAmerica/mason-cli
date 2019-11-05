import hashlib

import click
import requests


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


def log_failed_response(config, r, message):
    config.logger.debug('{}: {}'.format(message, r.status_code))
    _handle_status(config, r.status_code)

    if r.text:
        if _format_errors_new_type(config, r):
            return
        if _format_errors_old_type(config, r):
            return
        config.logger.error(r.text)


def _handle_status(config, status_code):
    if status_code == 400:
        config.logger.debug('Client made a bad request, failed.')
    elif status_code == 401:
        config.logger.error('User token is expired or user is unauthorized.')
    elif status_code == 403:
        config.logger.error('Access to domain is forbidden. Please contact support.')
    elif status_code == 404:
        config.logger.debug('Resource is unavailable, failed')
    elif status_code == 500:
        config.logger.debug('Mason service or resource is currently unavailable.')


def _format_errors_new_type(config, r):
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

        details = err_result['details']
        if type(details) is list:
            details = [detail['message'] for detail in details]
        config.logger.error('{}: {}'.format(err_result['error'], details))

        if 'itemized' in err_result:
            for item in err_result['itemized']:
                config.logger.error("{} (code: '{}')".format(item['message'], item['code']))
    except (KeyError, ValueError):
        return False

    return True


def _format_errors_old_type(config, r):
    try:
        details = r.json()['error']['details']
        config.logger.error(details)
    except (KeyError, ValueError):
        return False

    return True
