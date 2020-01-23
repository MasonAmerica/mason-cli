import os

import click
import requests
from tqdm import tqdm


class RequestHandler:
    def __init__(self, config):
        self.config = config

    def get(self, url, *args, **kwargs):
        return self._request_wrapper('get', url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._request_wrapper('post', url, *args, **kwargs)

    def put(self, url, binary, *args, **kwargs):
        binary_file = open(binary, 'rb')
        iterable = UploadInChunks(binary_file.name, chunksize=10)
        return self._request_wrapper(
            'put', url, data=IterableToFileAdapter(iterable), *args, **kwargs)

    def _request_wrapper(self, type, url, *args, **kwargs):
        self.config.logger.debug('Starting {} request to {} with payload {}'.format(
            type.upper(), url, kwargs.get('json')))
        r = self._safe_request(type, url, *args, **kwargs)
        self.config.logger.debug(
            'Finished request to {} with status code {} '
            'and response {}'.format(url, r.status_code, r.text))

        if r.status_code != 200:
            self._handle_failed_response(r)
        if r.text:
            return r.json()

    def _safe_request(self, type, *args, **kwargs):
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
                        self.config.logger.error(item['message'])
                        self.config.logger.info(
                            'Create a new project: '
                            'https://platform.bymason.com/controller/projects')
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
    def __init__(self, filename, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = int(chunksize)
        self.totalsize = os.stat(filename).st_size
        self.pbar = tqdm(total=self.totalsize, ncols=100, unit='kb', dynamic_ncols=True)

    def __iter__(self):
        with open(self.filename, 'rb') as file_to_upload:
            while True:
                data = file_to_upload.read(self.chunksize)
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

    # noinspection PyUnusedLocal
    def read(self, size=-1):
        return next(self.iterator, b'')

    def __len__(self):
        return self.length
