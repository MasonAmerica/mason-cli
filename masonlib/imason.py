import abc
from abc import abstractmethod

import six


@six.add_metaclass(abc.ABCMeta)
class IMason:
    """
    The main Mason interface. Provides methods that allow you to parse, register, build, and deploy
    artifacts.
    """

    @abstractmethod
    def set_id_token(self, id_token):
        """
        Public set method for id token.

        :param id_token: the id token to be utilized for authentication
        """

        pass

    @abstractmethod
    def set_access_token(self, access_token):
        """
        Public set method for access token.

        :param access_token: the access token to be utilized for authentication
        """

        pass

    @abstractmethod
    def validate_apk(self, apk):
        """
        Public apk parse method, returns true if supported artifact, false otherwise.

        :param apk: specify the path of the apk file
        """

        pass

    @abstractmethod
    def validate_media(self, name, type, version, binary):
        """
        Public media parse method, returns true if supported artifact, false otherwise.

        :param name: specify the name of the media artifact
        :param type: specify the type of the media artifact
        :param version: specify the unique version of the media artifact
        :param binary: specify the path of the media binary file
        """

        pass

    @abstractmethod
    def validate_os_config(self, config_yaml):
        """
        Public os parse method, returns true if supported artifact, false otherwise.

        :param config_yaml: specify the path of the os configuration yaml file
        """

        pass

    @abstractmethod
    def register(self, binary):
        """
        Register a given binary. Need to call one of the parse commands prior to invoking register
        to validate a given artifact and decorate it with the necessary metadata for service upload.

        :param binary: specify the path of the artifact file
        """

        pass

    @abstractmethod
    def build(self, project, version, block):
        """
        Public build method, returns true if build started, false otherwise.

        :param project: specify the name of the project to start a build for
        :param version: specify the version of the project for which to start a build for
        :param block: should the method block until the build has finished
        """

        pass

    @abstractmethod
    def deploy(self, item_type, name, version, group, push, no_https):
        """
        Public deploy method, returns true if item is deployed, false otherwise.

        :param item_type: specify the item type to be deployed
        :param name: specify the name of the item to be deployed
        :param version: specify the version of the item to be deployed
        :param group: specify the group to deploy the item to
        :param push: whether to push the deploy to the devices in the group
        :param no_https: whether deployments should be delivered to devices insecurely
        """

        pass

    @abstractmethod
    def stage(self, yaml, block):
        """
        Public stage method, returns true if the configuration was staged, false otherwise.
        The stage command effectively registers and and builds a given configuration.

        :param yaml: The yaml file which needs to be staged
        :param block: should the method block until the build has finished
        """

        pass

    @abstractmethod
    def authenticate(self, user, password):
        """
        Public authentication method, returns true if authed, false otherwise.

        :param user: specify a user as string
        :param password: specify a password as string
        """

        pass

    @abstractmethod
    def logout(self):
        """
        Public logout method, returns true if successfully logged out.
        """

        pass
