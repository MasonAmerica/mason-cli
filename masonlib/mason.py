import logging
import os

import click
import click_log

from masonlib import __version__
from masonlib.imason import IMason
from masonlib.platform import Platform

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'INFO').upper())
click_log.ClickHandler._use_stderr = False
click_log.basic_config(logger)


class Config(object):
    """
    Global config object, utilized to set verbosity of logging events
    and other flags.
    """

    def __init__(self):
        self.logger = logger


pass_config = click.make_pass_decorator(Config, ensure=True)


# noinspection PyUnusedLocal
def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    _show_version_info()
    ctx.exit()


@click.group()
@click.option('--version', '-V', is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback,
              help='Show the version and exit.')
@click.option('--access-token',
              help='Supply an access token for this command.')
@click.option('--id-token',
              help='Supply an ID token for this command.')
@click.option('--no-color', is_flag=True, default=False,
              help='Disable rich console output.')
@click.option('--debug', '-d', is_flag=True, default=False, hidden=True,
              help='Log diagnostic data.')
@click.option('--verbose', is_flag=True, hidden=True,
              help='Log verbose artifact and command details.')
@click_log.simple_verbosity_option(logger)
@pass_config
def cli(config, debug, verbose, id_token, access_token, no_color):
    """
    The Mason CLI provides command line tools to help you manage your configurations in the Mason
    Platform.
    """

    platform = Platform(config)
    config.mason = platform.get(IMason)
    if id_token:
        config.mason.set_id_token(id_token)
    if access_token:
        config.mason.set_access_token(access_token)

    if no_color:
        click_log.ColorFormatter.colors = {
            'error': {},
            'exception': {},
            'critical': {},
            'debug': {},
            'warning': {}
        }
    if verbose or debug:
        logger.warning('--debug and --verbose options are deprecated. Please use --verbosity debug '
                       'instead.')
        logger.setLevel('DEBUG')

    config.mason.check_for_updates()


@cli.group()
@click.option('--assume-yes', '--yes', '-y', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@pass_config
def register(config, assume_yes, skip_verify):
    """Register artifacts to the Mason Platform."""

    if skip_verify:
        logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify


@register.command()
@click.argument('configs', type=click.Path(exists=True), nargs=-1, required=True)
@pass_config
def config(config, configs):
    """
    Register config artifacts.

      CONFIG(S) describing a configuration to be registered to the Mason Platform.

    \b
    For example, register a single config:
      $ mason register config test.yml

    \b
    Or all in a subdirectory:
      $ mason register config configs/*.yml

    For more information on configs, view the full documentation here:
    https://docs.bymason.com/project-config/
    """

    for file in configs:
        logger.debug('Registering {}...'.format(file))
        config.mason.register_os_config(file)


@register.command()
@click.argument('apks', type=click.Path(exists=True), nargs=-1, required=True)
@pass_config
def apk(config, apks):
    """
    Register APK artifacts.

      APK(S) to be registered to the Mason Platform.

    \b
    For example, register a single APK:
      $ mason register apk test.apk

    \b
    Or all in a subdirectory:
      $ mason register apk apks/*.apk
    """

    for app in apks:
        logger.debug('Registering {}...'.format(app))
        config.mason.register_apk(app)


# TODO: add types when support for the deprecated param order is removed.
@register.command()
@click.argument('name')
@click.argument('type')
@click.argument('version')
@click.argument('media')
@pass_config
def media(config, name, type, version, media):
    """
    Register media artifacts.

    \b
      NAME of the media artifact.
      TYPE of the media artifact. One of:
        - bootanimation
      VERSION of the media artifact.
      MEDIA file to be uploaded.

    \b
    For example, register a boot animation:
      $ mason register media mason-test bootanimation 1 bootanimation.zip
    """

    if os.path.isfile(name):
        logger.warning('This command order is deprecated and will be removed. Use --help to see '
                       'up-to-date argument order.')

        # Media used to be the first argument
        old_media = name
        old_name = type
        old_type = version
        old_version = media
        name = old_name
        type = old_type
        version = old_version
        media = old_media

    logger.debug('Registering {}...'.format(media))
    config.mason.register_media(name, type, version, media)


@cli.command()
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.option('--turbo', is_flag=True, default=False,
              help='Enable fast Mason config builds (beta).')
@click.argument('project')
@click.argument('version', type=click.IntRange(min=0))
@pass_config
def build(config, block, turbo, project, version):
    """
    Build a registered project. Use the "register" command to upload artifacts for a project.

    \b
      PROJECT name.
      VERSION of the project.

    The name and version of the project can either be found in the config file you register, or in
    the Mason Console: https://platform.bymason.com/controller/projects/YOUR_PROJECT_NAME_HERE.

    \b
    For example, this registered project:
      os:
        name: mason-test
        version: 5

    \b
    can be built with:
      $ mason build mason-test 5
    """

    logger.debug('Starting build for {}:{}...'.format(project, version))
    config.mason.build(project, version, block, turbo)


@cli.command()
@click.option('--assume-yes', '--yes', '-y', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.option('--turbo', is_flag=True, default=False,
              help='Enable fast Mason config builds (beta).')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@click.argument('configs', type=click.Path(exists=True), nargs=-1, required=True)
@pass_config
def stage(config, assume_yes, block, turbo, skip_verify, configs):
    """
    Register and build (aka stage) a project.

      CONFIG(S) describing a configuration to be registered to the Mason Platform and then
    subsequently built.

    \b
    For example, register and build a single config:
      $ mason stage test.yml

    For more information on configs, view the full documentation here:
    https://docs.bymason.com/project-config/

    \b
    The stage command is equivalent to running:
      $ mason register config ...
      $ mason build ...
    """

    if skip_verify:
        logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify

    for file in configs:
        logger.debug('Staging {}...'.format(file))
        config.mason.stage(file, block, turbo)


@cli.group()
@click.option('--assume-yes', '--yes', '-y', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--push', '-p', is_flag=True, default=False,
              help='Push the deployment to devices in the field immediately.')
@click.option('--no-https', is_flag=True, default=False, hidden=True,
              help='Use insecure download links to enable caching via local proxies.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@pass_config
def deploy(config, assume_yes, push, no_https, skip_verify):
    """Deploy artifacts to groups."""

    if skip_verify:
        logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify
    config.push = push
    config.no_https = no_https


@deploy.command()
@click.argument('name')
@click.argument('version', type=click.IntRange(min=0))
@click.argument('groups', nargs=-1, required=True)
@pass_config
def config(config, name, version, groups):
    """
    Deploy config artifacts.

      NAME of the configuration to be deployed.
      VERSION of the configuration to be deployed.
      GROUP(S) to deploy the configuration to.

    \b
    For example, this registered configuration:
      os:
        name: mason-test
        version: 1

    \b
    can be deployed to the "development" group with:
      $ mason deploy config mason-test 1 development

    \b
    or deployed to multiple groups:
      $ mason deploy config mason-test 1 group1 group2 group3
    """

    for group in groups:
        logger.debug('Deploying {}:{}...'.format(name, version))
        config.mason.deploy('config', name, version, group, config.push, config.no_https)


@deploy.command()
@click.argument('name')
@click.argument('version', type=click.IntRange(min=0))
@click.argument('groups', nargs=-1, required=True)
@pass_config
def apk(config, name, version, groups):
    """
    Deploy APK artifacts.

    \b
      NAME is the package name of the apk to be deployed.
      VERSION code of the APK.
      GROUP(S) to deploy the APK to.

    \b
    For example, this registered APK:
      apps:
        - name: App Name
          package_name: com.test.app
          version_code: 1

    \b
    can be deployed to the "development" group with:
      $ mason deploy apk com.test.app 1 development

    \b
    or deployed to multiple groups:
      $ mason deploy apk com.test.app 1 group1 group2 group3
    """

    for group in groups:
        logger.debug('Deploying {}:{}...'.format(name, version))
        config.mason.deploy('apk', name, version, group, config.push, config.no_https)


@deploy.command()
@click.argument('name')
@click.argument('version', type=click.IntRange(min=0))
@click.argument('groups', nargs=-1, required=True)
@pass_config
def ota(config, name, version, groups):
    """
    Deploy ota artifacts.

    \b
      NAME of the ota to be deployed (usually "mason-os").
      VERSION of the ota.
      GROUP(S) to deploy the ota to.

    \b
    For example, deploy Mason OS 2.0.0 to the "development" group:
      $ mason deploy ota mason-os 2.0.0 development

    \b
    or to multiple groups:
      $ mason deploy ota mason-os 2.0.0 group1 group2 group3
    """

    for group in groups:
        logger.debug('Deploying {}:{}...'.format(name, version))
        config.mason.deploy('ota', name, version, group, config.push, config.no_https)


@cli.command()
@click.option('--username', '--user', '-u', prompt=True,
              help='Your Mason Platform username.')
@click.option('--password', '--pass', '-p', prompt=True, hide_input=True,
              help='Your Mason Platform password.')
@pass_config
def login(config, username, password):
    """Authenticate via username and password."""

    logger.debug('Authenticating ' + username)
    config.mason.login(username, password)
    logger.info('Successfully logged in.')


@cli.command()
@pass_config
def logout(config):
    """Log out of the Mason CLI."""

    config.mason.logout()
    logger.info('Successfully logged out.')


@cli.command(hidden=True)
def version():
    """Display the Mason CLI version."""

    _show_version_info()


def _show_version_info():
    logger.info('Mason CLI v{}'.format(__version__))
    logger.info('Copyright (C) 2019 Mason America (https://bymason.com)')
    logger.info('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')


if __name__ == '__main__':
    cli()
