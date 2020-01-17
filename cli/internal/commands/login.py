from cli.internal.commands.command import Command
from cli.internal.utils.remote import ApiError


class LoginCommand(Command):
    def __init__(self, config, api_key, username, password):
        self.config = config
        self.api_key = api_key
        self.username = username
        self.password = password

    def run(self):
        self.config.logger.debug('Authenticating ' + self.username)
        self._login()
        self.config.logger.info('Successfully logged in.')

    def _login(self):
        if self.api_key:
            self.config.auth_store['api_key'] = self.api_key

        try:
            user = self.config.api.login(self.username, self.password)
        except ApiError as e:
            e.exit(self.config)
            return

        self.config.auth_store['id_token'] = user.get('id_token')
        self.config.auth_store['access_token'] = user.get('access_token')

        self.config.auth_store.save()
