import hashlib
import colorama


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


def print_err(config, msg):
    if config.no_colorize:
        print msg
    else:
        print colorama.Fore.RED + msg


def print_msg(config, msg):
    if config.no_colorize:
        print msg
    else:
        print colorama.Fore.GREEN + msg


def format_errors(config, response):
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
    :param response: Text containing errors. Can be `None`
    """
    try:
        err_result = response.json()
        print_err(config, "Error: {} ('{}')".format(err_result['error'], err_result['details']))
        if 'itemized' in err_result:
            for item in err_result['itemized']:
                print_err(config, u"  \u25b6 {} (code: '{}')".format(item["message"], item["code"]))
    except ValueError:
        if response.text:
            print_err(config, response.text)
