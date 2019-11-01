import os
from sys import exit

import click
import colorama
import packaging.version
import requests

from masonlib import __version__
from masonlib.imason import IMason
from masonlib.platform import Platform


class Config(object):
    """
    Global config object, utilized to set verbosity of logging events
    and other flags.
    """

    def __init__(self):
        self.verbose = False
        self.no_colorize = False


pass_config = click.make_pass_decorator(Config, ensure=True)


def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    _print_version_info()
    ctx.exit()


@click.group()
@click.option('--version', '-V', is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback,
              help='Show the version and exit.')
@click.option('--debug', '-d', is_flag=True, default=False,
              help='Log diagnostic data.')
@click.option('--verbose', '-v', is_flag=True,
              help='Log verbose artifact and command details.')
@click.option('--access-token',
              help='Supply an access token for this command.')
@click.option('--id-token',
              help='Supply an ID token for this command.')
@click.option('--no-color', is_flag=True, default=False,
              help='Disable rich console output.')
@pass_config
def cli(config, debug, verbose, id_token, access_token, no_color):
    """
    The Mason CLI provides command line tools to help you manage your configurations in the Mason
    Platform.
    """

    _check_version()

    config.debug = debug
    config.verbose = verbose
    config.no_colorize = no_color
    if not no_color:
        colorama.init(autoreset=True)
    platform = Platform(config)
    config.mason = platform.get(IMason)
    config.mason.set_id_token(id_token)
    config.mason.set_access_token(access_token)


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
        if config.verbose:
            click.echo('Registering {}...'.format(app))
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
        if config.verbose:
            click.echo('Registering {}...'.format(file))
        if config.mason.parse_os_config(file):
            config.mason.register(file)


@register.command()
@click.argument('binary')
@click.argument('name')
@click.argument('type')
@click.argument('version')
@pass_config
def media(config, binary, name, type, version):
    """
    Register media artifacts.

    \b
      NAME of the media artifact.
      TYPE of the media artifact. One of:
        - bootanimation
      VERSION of the media artifact.
      BINARY file to be uploaded.

    \b
    For example, register a boot animation:
      $ mason register media bootanimation.zip bootanimation 1
    """

    if config.verbose:
        click.echo('Registering {}...'.format(binary))
    if config.mason.parse_media(name, type, version, binary):
        config.mason.register(binary)


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

    if config.verbose:
        click.echo('Starting build for {}:{}...'.format(project, version))
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
        if config.verbose:
            click.echo('Deploying {}:{}...'.format(name, version))
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
        if config.verbose:
            click.echo('Deploying {}:{}...'.format(name, version))
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
        if config.verbose:
            click.echo('Deploying {}:{}...'.format(name, version))
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
    if config.verbose:
        click.echo('Staging {}...'.format(yaml))
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

    if config.verbose:
        click.echo('Authenticating ' + username)
    if not config.mason.authenticate(username, password):
        exit('Unable to authenticate')
    else:
        click.echo('User authenticated.')


@cli.command()
@pass_config
def logout(config):
    """Log out of the Mason CLI."""

    if config.mason.logout():
        click.echo('Successfully logged out')


@cli.command(hidden=True)
def version():
    """Display the Mason CLI version."""

    _print_version_info()


def _print_version_info():
    click.echo('Mason CLI v{}'.format(__version__))
    click.echo('Copyright (C) 2019 Mason America (https://bymason.com)')
    click.echo('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')


def _check_version():
    r = requests.get('https://raw.githubusercontent.com/MasonAmerica/mason-cli/master/VERSION')
    if r.status_code == 200:
        if r.text:
            current_version = packaging.version.parse(__version__)
            remote_version = packaging.version.parse(r.text)
            if remote_version > current_version:
                if isMasonDocker():
                    upgrade_command = 'docker pull masonamerica/mason-cli:latest'
                else:
                    upgrade_command = 'pip install --upgrade git+https://git@github.com/MasonAmerica/mason-cli.git'
                print('\n==================== NOTICE ====================\n' \
                      'A newer version \'{}\' of the mason-cli is available.\n' \
                      'Run:\n' \
                      '    `{}`\n' \
                      'to upgrade to the latest version.\n' \
                      '\n' \
                      'Release notes: https://github.com/MasonAmerica/mason-cli/releases' \
                      '\n' \
                      '==================== NOTICE ====================\n'.format(remote_version,
                                                                                  upgrade_command))


def isMasonDocker():
    return bool(os.environ.get('MASON_CLI_DOCKER', False))


if __name__ == '__main__':
    cli()
