import click

from cli.internal.utils.constants import AUTH


def validate_credentials(config):
    if not AUTH['id_token'] or not AUTH['access_token']:
        config.logger.error('Not authenticated. Run \'mason login\' to sign in.')
        raise click.Abort()


def validate_version(config, version, type):
    try:
        version = int(version)
    except ValueError:
        config.logger.error("Error in {}: '{}' is not a number.".format(type, version))
        raise click.Abort()

    if not (0 < version < 2147483647):
        config.logger.error('The {} version cannot be negative or larger '
                            'than MAX_INT (2147483647).'.format(type))
        raise click.Abort()
