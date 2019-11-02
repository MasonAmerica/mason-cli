import inspect
import logging
import os
from sys import exit

import click
import click_log
import packaging.version
import requests

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

    _check_version()

    platform = Platform(config)
    config.mason = platform.get(IMason)
    config.mason.set_id_token(id_token)
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


@cli.group()
@click.option('--skip-verify', '-y', '-s', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@pass_config
def register(config, skip_verify):
    """Register artifacts to the Mason Platform."""

    config.skip_verify = skip_verify


@register.command()
@click.argument('apks', nargs=-1)
@pass_config
def apk(config, apks):
    """
    Register APK artifacts.

      APKS to be registered to the Mason Platform.

    \b
    For example, register a single APK:
      $ mason register apk test.apk

    \b
    Or all in a subdirectory:
      $ mason register apk apks/*.apk
    """

    for app in apks:
        logger.debug('Registering {}...'.format(app))
        if config.mason.parse_apk(app):
            config.mason.register(app)


@register.command()
@click.argument('configs', nargs=-1)
@pass_config
def config(config, configs):
    """
    Register config artifacts.

      CONFIGS describing a configuration to be registered to the Mason Platform.

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
        if config.mason.parse_os_config(file):
            config.mason.register(file)


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
    if config.mason.parse_media(name, type, version, media):
        config.mason.register(media)


@cli.command()
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.argument('project')
@click.argument('version')
@pass_config
def build(config, block, project, version):
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
    if not config.mason.build(project, version, block):
        exit('Unable to start build')


@cli.group()
@click.option('--skip-verify', '-y', '-s', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--push', '-p', is_flag=True, default=False,
              help='Push the deployment to devices in the field immediately.')
@click.option('--no-https', is_flag=True, default=False, hidden=True,
              help='Use insecure download links to enable caching via local proxies.')
@pass_config
def deploy(config, skip_verify, push, no_https):
    """Deploy artifacts to groups."""

    config.skip_verify = skip_verify
    config.push = push
    config.no_https = no_https


@deploy.command()
@click.argument('name')
@click.argument('version')
@click.argument('groups', nargs=-1)
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
        if not config.mason.deploy("apk", name, version, group, config.push, config.no_https):
            exit('Unable to deploy item')


@deploy.command()
@click.argument('name')
@click.argument('version')
@click.argument('groups', nargs=-1)
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
        if not config.mason.deploy("ota", name, version, group, config.push, config.no_https):
            exit('Unable to deploy item')


@deploy.command()
@click.argument('name')
@click.argument('version')
@click.argument('groups', nargs=-1)
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
        if not config.mason.deploy("config", name, version, group, config.push, config.no_https):
            exit('Unable to deploy item')


@cli.command()
@click.option('--skip-verify', '-y', '-s', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.argument('yaml')
@pass_config
def stage(config, skip_verify, block, yaml):
    """
    Register and build (aka stage) a project.

      YAML describing a configuration to be registered to the Mason Platform and then subsequently
    built.

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

    config.skip_verify = skip_verify
    logger.debug('Staging {}...'.format(yaml))
    if config.mason.parse_os_config(yaml):
        config.mason.stage(yaml, block)


@cli.command()
@click.option('--username', '--user', '-u', prompt=True,
              help='Your Mason Platform username.')
@click.option('--password', '--pass', '-p', prompt=True, hide_input=True,
              help='Your Mason Platform password.')
@pass_config
def login(config, username, password):
    """Authenticate via username and password."""

    logger.debug('Authenticating ' + username)
    if not config.mason.authenticate(username, password):
        exit('Unable to authenticate')
    else:
        logger.info('User authenticated.')


@cli.command()
@pass_config
def logout(config):
    """Log out of the Mason CLI."""

    if config.mason.logout():
        logger.info('Successfully logged out.')
    else:
        logger.info('Already logged out.')


@cli.command(hidden=True)
def version():
    """Display the Mason CLI version."""

    _show_version_info()


def _show_version_info():
    logger.info('Mason CLI v{}'.format(__version__))
    logger.info('Copyright (C) 2019 Mason America (https://bymason.com)')
    logger.info('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')


def _check_version():
    try:
        r = requests.get('https://raw.githubusercontent.com/MasonAmerica/mason-cli/master/VERSION')
    except requests.RequestException as e:
        logger.debug('Failed to fetch latest version: {}'.format(e))
        return

    if r.status_code == 200 and r.text:
        current_version = packaging.version.parse(__version__)
        remote_version = packaging.version.parse(r.text)
        if remote_version > current_version:
            if isMasonDocker():
                upgrade_command = 'docker pull masonamerica/mason-cli:latest'
            else:
                upgrade_command = 'pip install --upgrade git+https://git@github.com/MasonAmerica/mason-cli.git'

            logger.info(inspect.cleandoc("""
            ==================== NOTICE ====================
            A newer version '{}' of the mason-cli is available.
            Run:
              $ {}
            to upgrade to the latest version.

            Release notes: https://github.com/MasonAmerica/mason-cli/releases
            ==================== NOTICE ====================
            """.format(remote_version, upgrade_command)))
            logger.info('')
    else:
        logger.debug('Failed to fetch latest version: {}'.format(r))


def isMasonDocker():
    return bool(os.environ.get('MASON_CLI_DOCKER', False))


if __name__ == '__main__':
    cli()
