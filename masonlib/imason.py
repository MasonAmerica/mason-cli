import abc, six

from abc import abstractmethod

@six.add_metaclass(abc.ABCMeta)
class IMason():
    """ The main Mason interface. Provides methods that allow you to parse, register, build, and deploy artifacts.

        :param config: A global config object detailing verbosity and extra functions."""

    @abstractmethod
    def set_id_token(self, id_token):
        """ Public set method for id token
            :param id_token: the id token to be utilized for authentication"""
        pass

    @abstractmethod
    def set_access_token(self, access_token):
        """ Public set method for access token
            :param access_token: the access token to be utilized for authentication"""
        pass

    @abstractmethod
    def parse_apk(self, apk):
        """ Public apk parse method, returns true if supported artifact, false otherwise

            :param apk: specify the path of the apk file
            :rtype: boolean"""
        pass

    @abstractmethod
    def parse_media(self, name, type, version, binary):
        """ Public media parse method, returns true if supported artifact, false otherwise

            :param name: specify the name of the media artifact
            :param type: specify the type of the media artifact
            :param version: specify the unique version of the media artifact
            :param binary: specify the path of the media binary file
            :rtype: boolean"""
        pass

    @abstractmethod
    def parse_os_config(self, config_yaml):
        """ Public os parse method, returns true if supported artifact, false otherwise

            :param config_yaml: specify the path of the os configuration yaml file
            :rtype: boolean"""
        pass

    @abstractmethod
    def register(self, binary, legacy):
        """ Register a given binary. Need to call one of the parse commands prior to invoking register to validate
            a given artifact and decorate it with the necessary metadata for service upload.

            :param binary: specify the path of the artifact file
            :param legacy: if true, use the legacy code path for registering artifacts"""
        pass

    @abstractmethod
    def build(self, project, version):
        """ Public build method, returns true if build started, false otherwise

            :param project: specify the name of the project to start a build for
            :param version: specify the version of the project for which to start a build for
            :rtype: boolean"""
        pass

    @abstractmethod
    def deploy(self, item_type, name, version, group, push):
        """ Public deploy method, returns true if item is deployed, false otherwise

            :param item_type: specify the item type to be deployed
            :param name: specify the name of the item to be deployed
            :param version: specify the version of the item to be deployed
            :param group: specify the group to deploy the item to
            :param push: whether to push the deploy to the devices in the group
            :rtype boolean"""
        pass

    @abstractmethod
    def stage(self, yaml):
        """ Public stage method, returns true if the configuration was staged, false otherwise.
            The stage command effectively registers and and builds a given configuration.

            :param yaml: The yaml file which needs to be staged
            :rtype boolean"""
        pass

    @abstractmethod
    def authenticate(self, user, password):
        """ Public authentication method, returns true if authed, false otherwise

            :param user: specify a user as string
            :param password: specify a password as string
            :rtype: boolean"""
        pass

    @abstractmethod
    def logout(self):
        """ Public logout method, returns true if successfully logged out
            :rtype: boolean"""
        pass
