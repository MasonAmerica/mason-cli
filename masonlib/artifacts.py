import zipfile

class Media(object):
    def __init__(self, name, type, version, binary):
        self.name = name
        self.type = type
        self.version = version
        self.binary = binary
        self.details = None

    def is_valid_media(self):
        if self.type == 'bootanimation':
            return self.__validate_bootanimation()
        else:
            return False

    def __validate_bootanimation(self):
        with zipfile.ZipFile(self.binary) as zip_file:
            ret = zip_file.testzip()
            desc = zip_file.read('desc.txt')
            with zip_file.open('desc.txt') as filename:
                self.details = filename.readlines()
            if not desc:
                return False
        return ret is None