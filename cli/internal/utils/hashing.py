import hashlib


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
