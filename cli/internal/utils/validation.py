import click

from cli.config import Config


def validate_credentials(config: Config):
    if not config.auth_store['id_token'] or not config.auth_store['access_token']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_api_key(config: Config):
    if not config.auth_store['api_key']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_artifact_version(config: Config, version, type: str):
    if version == 'latest':
        return
    if version is None:
        config.logger.error("Invalid {}: version not found.".format(type))
        raise click.Abort()

    try:
        version = int(version)
    except (TypeError, ValueError):
        config.logger.error("Error in {}: '{}' is not a number.".format(type, version))
        raise click.Abort()

    if not (0 < version < 2147483647):
        config.logger.error('The {} version cannot be negative or larger '
                            'than MAX_INT (2147483647).'.format(type))
        raise click.Abort()
