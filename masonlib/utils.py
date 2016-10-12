# COPYRIGHT MASONAMERICA
import hashlib

class Utils(object):
    @staticmethod
    def hash_file(filename, type, asHex):
        if type == 'sha1':
            h = hashlib.sha1()
        else:
            h = hashlib.md5()

        with open(filename, 'rb') as file:
            # loop till the end of the file
            chunk = 0
            while chunk != b'':
                # read only 1024 bytes at a time
                chunk = file.read(1024)
                h.update(chunk)

        # return the hex representation of digest
        if asHex:
            return h.hexdigest()
        else:
            # return regular digest
            return h.digest()