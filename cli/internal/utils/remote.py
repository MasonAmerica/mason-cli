import os
from json.decoder import JSONDecodeError

import click
import requests
from tqdm import tqdm

from cli.internal.utils.logging import LazyLog


class RequestHandler:
    def __init__(self, config):
        self.config = config

    def get(self, url, *args, **kwargs):
        return self._request_wrapper('get', url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._request_wrapper('post', url, *args, **kwargs)

    def put(self, url, binary, *args, **kwargs):
        binary_file = open(binary, 'rb')
        iterable = UploadInChunks(binary_file.name)
        return self._request_wrapper(
            'put', url, data=IterableToFileAdapter(iterable), *args, **kwargs)

    def _request_wrapper(self, type, url, *args, **kwargs):
        self.config.logger.debug(LazyLog(lambda: 'Starting {} request to {} with payload {}'.format(
            type.upper(), url, kwargs.get('json'))))
        r = self._safe_request(type, url, *args, **kwargs)
        self.config.logger.debug(LazyLog(
            lambda: 'Finished request to {} with status code {} '
                    'and response {}'.format(url, r.status_code, r.text)))

        if not r.ok:
            self._handle_failed_response(r)
        if r.text:
            try:
                return r.json()
            except JSONDecodeError as e:
                self.config.logger.debug(e)
                return r.text

    def _safe_request(self, type, *args, **kwargs) -> requests.Response:
        func = getattr(requests, type)
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            self.config.logger.debug('{} request to {} failed: {}'.format(type.upper(), args[0], e))
            raise ApiError('Network request failed. Check you internet connection.')

    def _handle_failed_response(self, r):
        self._handle_status(r.status_code)

        if r.text:
            self._handle_errors_new_type(r)
            self._handle_errors_old_type(r)
            raise ApiError(r.text)

        raise ApiError()

    def _handle_status(self, status_code):
        if status_code == 400:
            self.config.logger.debug('Client made a bad request, failed.')
        elif status_code == 401:
            raise ApiError("Unauthorized: session expired or access denied. Run 'mason login' to "
                           "start a new session.")
        elif status_code == 403:
            self.config.logger.error('Access to domain is forbidden. Please contact support.')
        elif status_code == 404:
            self.config.logger.debug('Resource is unavailable, failed')
        elif status_code == 500:
            self.config.logger.debug('Mason service or resource is currently unavailable.')

    def _handle_errors_new_type(self, r):
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

        If JSON is not detected, just prints `body` as text. Colorizes in red if the option is set
        in `config`.

        :param r: Response
        """

        try:
            err_result = r.json()
            self.config.logger.debug(err_result)

            if 'itemized' in err_result:
                for item in err_result['itemized']:
                    if item['code'] == '8f92ccpl':
                        try:
                            project_id = item['message'].split(' project ', 1)[1] \
                                .split(' was not ')[0]
                        except Exception as e:
                            self.config.logger.debug(e)
                            project_id = ''

                        base_url = self.config.endpoints_store['console_projects_url']
                        url = base_url + '/_create?name={}'.format(project_id)

                        self.config.logger.error(item['message'])
                        self.config.logger.info('Create a new project: {}'.format(url))

                        raise ApiError()
                    else:
                        self.config.logger.error(
                            "{} (code: '{}')".format(item['message'], item['code']))

            details = err_result['details']
            if type(details) is list:
                details = [detail['message'] for detail in details]
            raise ApiError('{}: {}'.format(err_result['error'], details))
        except (KeyError, ValueError):
            return

    def _handle_errors_old_type(self, r):
        try:
            details = r.json()['error']['details']
            raise ApiError(details)
        except (KeyError, ValueError):
            try:
                raise ApiError(r.json()['data'])
            except (KeyError, ValueError):
                try:
                    raise ApiError(r.json()['message'])
                except (KeyError, ValueError):
                    return


class ApiError(Exception):
    def __init__(self, message=None):
        self.message = message

    def exit(self, config):
        if self.message:
            config.logger.error(self.message)
        raise click.Abort()


class UploadInChunks(object):
    def __init__(self, path):
        self.path = path
        self.num_bytes = os.path.getsize(path)
        self.chunk_size = 5120  # 5KB == 2^10 * 5

        self.progress = tqdm(
            total=self.num_bytes,
            ncols=100,
            dynamic_ncols=True,
            unit='B',
            unit_scale=True
        )

    def __iter__(self):
        with open(self.path, 'rb') as file_to_upload:
            while True:
                data = file_to_upload.read(self.chunk_size)
                if not data:
                    self.progress.close()
                    break

                self.progress.update(len(data))
                yield data

    def __len__(self):
        return self.num_bytes


class IterableToFileAdapter(object):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    # noinspection PyUnusedLocal
    def read(self, size=-1):
        return next(self.iterator, b'')

    def __len__(self):
        return self.length
