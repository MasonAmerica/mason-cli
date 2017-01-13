#!/usr/bin/env python2
import getpass
import pkg_resources
import click
import requests

from masonlib.platform import Platform
from masonlib.imason import IMason

class Config(object):
    """
    Global config object, utilized to set verbosity of logging events
    """

    def __init__(self):
        self.verbose = False
        self.__check_version()

    def __check_version(self):
        r = requests.get('https://raw.githubusercontent.com/MasonAmerica/mason-cli/master/VERSION')
        current_version = float(pkg_resources.require("mason-cli")[0].version)
        if r.status_code == 200:
            if r.text:
                remote_version = float(r.text)
                if remote_version > current_version:
                    print '\n==================== NOTICE ====================\n' \
                          'A newer version of the mason-cli is available.\n' \
                          'Run:\n' \
                          '    `pip install --upgrade git+git://git@github.com/MasonAmerica/mason-cli.git`\n' \
                          'to upgrade to the latest version.\n' \
                          '==================== NOTICE ====================\n'

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--verbose', '-v', help='show verbose artifact and command details', is_flag=True)
@click.option('--access_token', help='optional access token if already available')
@click.option('--id_token', help='optional id token if already available')
@pass_config
def cli(config, verbose, id_token, access_token):
    """mason-cli provides command line interfaces that allow you to register, query, build, and deploy
your configurations and packages to your devices in the field."""
    config.verbose = verbose
    platform = Platform(config)
    config.mason = platform.get(IMason)
    config.mason.set_id_token(id_token)
    config.mason.set_access_token(access_token)

@cli.group()
@click.option('--skip-verify', '-s', is_flag=True, help='skip verification of artifact details')
@pass_config
def register(config, skip_verify):
    """Register artifacts to the mason platform"""
    config.skip_verify = skip_verify

@register.command()
@click.argument('apks', nargs=-1)
@pass_config
def apk(config, apks):
    """Register apk artifacts"""
    for app in apks:
        if config.verbose:
            click.echo('Registering ' + app + '...')
        if config.mason.parse_apk(app):
            config.mason.register(app)

@register.command()
@click.argument('yaml')
@pass_config
def config(config, yaml):
    """Register config artifacts"""
    if config.verbose:
        click.echo('Registering ' + yaml + '...')
    if config.mason.parse_os_config(yaml):
        config.mason.register(yaml)

@register.command()
@click.argument('binary')
@click.option('--name', '-n', help='the name for the media artifact', default=None)
@click.option('--type', '-t', help='the type of media artifact', default=None)
@click.option('--version', '-v', help='the version for the media artifact', default=None)
@pass_config
def media(config, binary, name, type, version):
    """Register media artifacts"""
    if not name:
        exit('Name is required for media')
    if not type:
        exit('Type is required for media')
    if not version:
        exit('Version is required for media')

    if config.verbose:
        click.echo('Registering ' + binary + '...')
    if config.mason.parse_media(name, type, version, binary):
        config.mason.register(binary)

@cli.command()
@click.argument('project')
@click.argument('version')
@pass_config
def build(config, project, version):
    """Build a registered project"""
    if config.verbose:
        click.echo('Starting build for ' + project + ':' + version)
    if not config.mason.build(project, version):
        exit('Unable to start build')

@cli.group()
@click.option('--skip-verify', '-s', is_flag=True, help='skip verification of deployment')
@pass_config
def deploy(config, skip_verify):
    """Register artifacts to the mason platform"""
    config.skip_verify = skip_verify

@deploy.command()
@click.argument('name')
@click.argument('version')
@click.argument('group')
@pass_config
def apk(config, name, version, group):
    """Deploy apk artifacts"""
    if config.verbose:
        click.echo('Deploying ' + name + '...')
    if not config.mason.deploy("apk", name, version, group):
        exit('Unable to deploy item')

@deploy.command()
@click.argument('name')
@click.argument('version')
@click.argument('group')
@pass_config
def config(config, name, version, group):
    """Deploy apk artifacts"""
    if config.verbose:
        click.echo('Deploying ' + name + '...')
    if not config.mason.deploy("config", name, version, group):
        exit('Unable to deploy item')

@cli.command()
@click.option('--user', default=None, help='pass in user')
@click.option('--password', default=None, help='pass in password')
@pass_config
def login(config, user, password):
    """Authenticate via user/password"""
    if not user or not password:
        # Prompt for user name
        response = raw_input('User: ')

        # Exit on empty user
        if not response:
            exit('Authentication requires a valid user')

        user = response

        # Prompt for password
        response = getpass.getpass()

        # Exit on empty password
        if not response:
            exit('Authentication requires a valid password')

        password = response
    if config.verbose:
        click.echo('Authing ' + user)
    if not config.mason.authenticate(user, password):
        exit('Unable to authenticate')
    else:
        click.echo('User authenticated.')

@cli.command()
@pass_config
def logout(config):
    """Log out of current session"""
    if config.mason.logout():
        click.echo('Successfully logged out')

@cli.command()
def version():
    """Display mason-cli version"""
    try:
        version = pkg_resources.require("mason-cli")[0].version
        click.echo('mason (Mason America) ' + version)
        click.echo('Copyright (C) 2016 Mason America')
        click.echo('License Apache 2.0 <https://www.apache.org/licenses/LICENSE-2.0>')
        click.echo('Originally written by Adnan Begovic')
    except pkg_resources.DistributionNotFound:
        click.echo('Unable to retrieve version information')

if __name__ == '__main__':
    cli()
