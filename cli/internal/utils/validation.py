import click


def validate_credentials(config):
    if not config.auth_store['id_token'] or not config.auth_store['access_token']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_api_key(config):
    if not config.auth_store['api_key']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_artifact_version(config, version, type):
    if version == 'latest':
        return

    try:
        version = int(version)
    except (TypeError, ValueError):
        config.logger.error("Error in {}: '{}' is not a number.".format(type, version))
        raise click.Abort()

    if not (0 < version < 2147483647):
        config.logger.error('The {} version cannot be negative or larger '
                            'than MAX_INT (2147483647).'.format(type))
        raise click.Abort()
