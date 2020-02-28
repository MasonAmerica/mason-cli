from cli.config import Config
from cli.internal.commands.command import Command


class LoginCommand(Command):
    def __init__(self, config: Config, api_key: str, username: str, password: str):
        super(LoginCommand, self).__init__(config)

        self.api_key = api_key
        self.username = username
        self.password = password

    @Command.helper('login')
    def run(self):
        self.config.logger.debug('Authenticating ' + self.username)
        self._login()
        self.config.logger.info('Successfully logged in.')

    def _login(self):
        if self.api_key:
            self.config.auth_store['api_key'] = self.api_key

        user = self.config.api.login(self.username, self.password)

        self.config.auth_store['id_token'] = user.get('id_token')
        self.config.auth_store['access_token'] = user.get('access_token')

        self.config.auth_store.save()
