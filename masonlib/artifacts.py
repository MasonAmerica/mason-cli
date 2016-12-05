class Artifact(object):

    def is_valid(self):
        raise NotImplementedError("Should have implemented this")

    def get_content_type(self):
        raise NotImplementedError("Should have implemented this")

    def get_type(self):
        raise NotImplementedError("Should have implemented this")

    def get_sub_type(self):
        raise NotImplementedError("Should have implemented this")

    def get_name(self):
        raise NotImplementedError("Should have implemented this")

    def get_version(self):
        raise NotImplementedError("Should have implemented this")

    def get_registry_meta_data(self):
        raise NotImplementedError("Should have implemented this")

    def get_details(self):
        raise NotImplementedError("Should have implemented this")