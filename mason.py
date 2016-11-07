#!/usr/bin/env python2
# COPYRIGHT MASONAMERICA
import click
import getpass
import pkg_resources

from masonlib.mason import Mason

## Global Config
class Config(object):

    def __init__(self):
        self.verbose = False

pass_config = click.make_pass_decorator(Config, ensure=True)

# MAIN CLI INTERFACE
@click.group()
@click.option('--verbose', is_flag=True)
@click.option('--access_token', help='optional access token if already available')
@click.option('--id_token', help='optional id token if already available')
@pass_config
def cli(config, verbose, id_token, access_token):
    """mason-cli provides command line interfaces that allow you to publish, query, and deploy
your configurations and packages to your devices in the field."""
    config.verbose = verbose
    config.mason = Mason(config)
    config.mason.id_token = id_token
    config.mason.access_token = access_token

# PUBLISH INTERFACE
@cli.command()
@click.argument("artifact")
@click.option('--name', default=None, help='optional name for the artifact')
@click.option('--skip-verify', '-s', is_flag=True, help='skip verification of artifact details')
@pass_config
def publish(config, name, skip_verify, artifact):
    """Upload artifacts"""
    if config.verbose:
        click.echo('Publishing ' + artifact + '...')
        if name:
            click.echo('Optional name: ' + name)
    if config.mason.parse(artifact):
        if not skip_verify:
            response = raw_input('Continue publish? (y)')
            if not response or response == 'y':
                if not config.mason.publish(artifact):
                    exit('Unable to publish artifact')
        else:
            if not config.mason.publish(artifact):
                exit('Unable to publish artifact')
            else:
                click.echo('Artifact successfully uploaded.')

# AUTHENTICATION INTERFACE
@cli.command()
@click.option('--user', default=None, help='pass in user')
@click.option('--password', default=None, help='pass in password')
@pass_config
def auth(config, user, password):
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

# VERSION INTERFACE
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
