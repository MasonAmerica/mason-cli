import hashlib


class Utils(object):

    @staticmethod
    def hash_file(filename, type_of_hash, as_hex):
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
