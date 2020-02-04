import logging
import os

import click
import click_log

from cli.internal.apis.mason import MasonApi
from cli.internal.commands.build import BuildCommand
from cli.internal.commands.deploy import DeployApkCommand
from cli.internal.commands.deploy import DeployConfigCommand
from cli.internal.commands.deploy import DeployOtaCommand
from cli.internal.commands.init import InitCommand
from cli.internal.commands.login import LoginCommand
from cli.internal.commands.logout import LogoutCommand
from cli.internal.commands.register import RegisterApkCommand
from cli.internal.commands.register import RegisterConfigCommand
from cli.internal.commands.register import RegisterMediaCommand
from cli.internal.commands.register import RegisterProjectCommand
from cli.internal.commands.stage import StageCommand
from cli.internal.commands.version import VersionCommand
from cli.internal.commands.xray import XrayDesktopCommand
from cli.internal.commands.xray import XrayInstallCommand
from cli.internal.commands.xray import XrayLogcatCommand
from cli.internal.commands.xray import XrayPullCommand
from cli.internal.commands.xray import XrayPushCommand
from cli.internal.commands.xray import XrayShellCommand
from cli.internal.commands.xray import XrayUninstallCommand
from cli.internal.utils import mason_types
from cli.internal.utils.constants import AUTH
from cli.internal.utils.constants import ENDPOINTS
from cli.internal.utils.constants import LOG_PROTOCOL_TRACE
from cli.internal.utils.mason_types import AliasedGroup
from cli.internal.utils.remote import RequestHandler


class Config(object):
    """
    Global config object, utilized to set verbosity of logging events
    and other flags.
    """

    def __init__(self, logger=None, auth_store=AUTH, endpoints_store=ENDPOINTS, api=None):
        logger = logger or logging.getLogger(__name__)
        api = api or MasonApi(RequestHandler(self), auth_store, endpoints_store)

        self.logger = logger
        self.auth_store = auth_store
        self.endpoints_store = endpoints_store
        self.api = api


pass_config = click.make_pass_decorator(Config, ensure=True)


def install_logger(logger, level):
    logger.setLevel(level)
    click_log.ClickHandler._use_stderr = False
    click_log.basic_config(logger)
    return logger


# noinspection PyUnusedLocal
def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    config = ctx.ensure_object(Config)
    install_logger(config.logger, 'INFO')

    command = VersionCommand(config)
    command.run()

    ctx.exit()


# noinspection PyUnusedLocal
def _handle_set_level(ctx, param, value):
    default_level = os.environ.get('LOGLEVEL', 'INFO').upper()
    if default_level.isdigit():
        default_level = int(default_level)
    logger = install_logger(ctx.ensure_object(Config).logger, default_level)

    if not value or ctx.resilient_parsing:
        return

    if value.upper() == "TRACE":
        logger.setLevel(LOG_PROTOCOL_TRACE)
        return
    if value.isdigit():
        logger.setLevel(int(value))
        return

    x = getattr(logging, value.upper(), None)
    if x is None:
        raise click.BadParameter(
            'Must be CRITICAL, ERROR, WARNING, INFO or DEBUG, not {}'
        )
    logger.setLevel(x)


@click.group(cls=AliasedGroup)
@click.option('--version', '-V', is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback,
              help='Show the version and exit.')
@click.option('--api-key', '--token',
              help='Supply an access token for this command.')
@click.option('--access-token',
              help='Supply an access token for this command.', hidden=True)
@click.option('--id-token',
              help='Supply an ID token for this command.', hidden=True)
@click.option('--no-color', is_flag=True, default=False,
              help='Disable rich console output.')
@click.option('--debug', '-d', is_flag=True, default=False, hidden=True,
              help='Log diagnostic data.')
@click.option('--verbose', is_flag=True, hidden=True,
              help='Log verbose artifact and command details.')
@click.option('--verbosity', '-v', expose_value=False, is_eager=True, callback=_handle_set_level,
              help='Either CRITICAL, ERROR, WARNING, INFO or DEBUG')
@pass_config
def cli(config, debug, verbose, api_key, id_token, access_token, no_color):
    """
    The Mason CLI provides command line tools to help you manage your configurations in the Mason
    Platform.

    \b
    Full docs: https://docs.bymason.com/
    """

    command = InitCommand(config, debug, verbose, no_color, api_key, id_token, access_token)
    command.run()


@cli.group(cls=AliasedGroup)
@click.option('--assume-yes', '--yes', '-y', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@pass_config
def register(config, assume_yes, skip_verify):
    """
    Register artifacts to the Mason Platform.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register
    """

    if skip_verify:
        config.logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify


@register.command()
@click.argument('context', type=click.Path(exists=True, file_okay=False), required=True,
                default='.')
@pass_config
def project(config, context):
    """
    Register whole projects.

      CONTEXT pointing the project directory. Defaults to the current directory.

    \b
    Example:
      $ mason register project

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-project
    """

    command = RegisterProjectCommand(config, context)
    command.run()


@register.command('config')
@click.argument('configs', type=click.Path(exists=True, dir_okay=False), nargs=-1, required=True)
@pass_config
def register_config(config, configs):
    """
    Register config artifacts.

      CONFIG(S) describing a configuration to be registered to the Mason Platform.

    \b
    For example, register a single config:
      $ mason register config test.yml

    \b
    Or all in a subdirectory:
      $ mason register config configs/*.yml

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-config
    """

    command = RegisterConfigCommand(config, configs)
    command.run()


@register.command('apk')
@click.argument('apks', type=click.Path(exists=True, dir_okay=False), nargs=-1, required=True)
@pass_config
def register_apk(config, apks):
    """
    Register APK artifacts.

      APK(S) to be registered to the Mason Platform.

    \b
    For example, register a single APK:
      $ mason register apk test.apk

    \b
    Or all in a subdirectory:
      $ mason register apk apks/*.apk

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-apk
    """

    command = RegisterApkCommand(config, apks)
    command.run()


@register.group(cls=AliasedGroup)
def media():
    """
    Register media artifacts.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-media
    """

    pass


@media.command()
@click.argument('name')
@click.argument('version', type=mason_types.Version())
@click.argument('media', type=click.Path(exists=True, dir_okay=False))
@pass_config
def bootanimation(config, name, version, media):
    """
    Register media artifacts.

    \b
      NAME of the media artifact.
      VERSION of the media artifact.
      MEDIA file to be uploaded.

    \b
    For example, register a boot animation:
      $ mason register media bootanimation mason-test 1 bootanimation.zip

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-media-bootanimation
    """

    command = RegisterMediaCommand(config, name, 'bootanimation', version, media)
    command.run()


@cli.command()
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.option('--turbo/--no-turbo', is_flag=True, default=True,
              help='Enable fast Mason config builds (beta).')
@click.option('--mason-version', hidden=True, help='Pick a specific Mason OS version.')
@click.argument('project')
@click.argument('version', type=click.IntRange(min=0))
@pass_config
def build(config, block, turbo, mason_version, project, version):
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

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-build
    """

    command = BuildCommand(config, project, version, block, turbo, mason_version)
    command.run()


@cli.command()
@click.option('--assume-yes', '--yes', '-y', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.option('--turbo/--no-turbo', is_flag=True, default=True,
              help='Enable fast Mason config builds (beta).')
@click.option('--mason-version', hidden=True, help='Pick a specific Mason OS version.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@click.argument('configs', type=click.Path(exists=True, dir_okay=False), nargs=-1, required=True)
@pass_config
def stage(config, assume_yes, block, turbo, mason_version, skip_verify, configs):
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

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-stage
    """

    if skip_verify:
        config.logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify

    command = StageCommand(config, configs, block, turbo, mason_version)
    command.run()


@cli.group(cls=AliasedGroup)
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
    """
    Deploy artifacts to groups.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy
    """

    if skip_verify:
        config.logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or skip_verify
    config.push = push
    config.no_https = no_https


@deploy.command('config')
@click.argument('name')
@click.argument('version', type=mason_types.Version())
@click.argument('groups', nargs=-1, required=True)
@pass_config
def deploy_config(config, name, version, groups):
    """
    Deploy config artifacts.

    \b
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

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy-config
    """

    command = DeployConfigCommand(config, name, version, groups)
    command.run()


@deploy.command('apk')
@click.argument('name')
@click.argument('version', type=mason_types.Version())
@click.argument('groups', nargs=-1, required=True)
@pass_config
def deploy_apk(config, name, version, groups):
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

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy-apk
    """

    command = DeployApkCommand(config, name, version, groups)
    command.run()


@deploy.command()
@click.argument('name')
@click.argument('version')
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

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy-ota
    """

    if name != 'mason-os':
        config.logger.warning("Unknown name '{0}' for 'ota' deployments. "
                              "Forcing it to 'mason-os'".format(name))
        name = 'mason-os'

    command = DeployOtaCommand(config, name, version, groups)
    command.run()


@cli.group(cls=AliasedGroup)
@click.argument('device')
@pass_config
def xray(config, device):
    """
    Use XRay to connect with services on the device.

    \b
      DEVICE to connect with (full device identifier).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray
    """

    config.device = device


@xray.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@pass_config
def logcat(config, args):
    """
    View streaming logs from the device.

    \b
      DEVICE to connect with (full device identifier).
      ARGS supplied to logcat (optional, see https://d.android.com/studio/command-line/logcat).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-logcat
    """

    command = XrayLogcatCommand(config, args)
    command.run()


@xray.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@pass_config
def shell(config, command):
    """
    Open a shell and run commands on the device.

    \b
      DEVICE to connect with (full device identifier).
      COMMAND to run (optional, if empty an interactive shell is opened).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-shell
    """

    command = XrayShellCommand(config, command)
    command.run()


@xray.command()
@click.argument('local', type=click.Path(exists=True, file_okay=True, readable=True))
@click.argument('remote', required=False)
@pass_config
def push(config, local, remote):
    """
    Push files to the device.

    \b
      DEVICE to connect with (full device identifier).
      LOCAL path of the file to be pushed.
      REMOTE path of the destination file.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-push
    """

    command = XrayPushCommand(config, local, remote)
    command.run()


@xray.command()
@click.argument('remote')
@click.argument('local', type=click.Path(dir_okay=True), required=False)
@pass_config
def pull(config, remote, local):
    """
    Pull files from the device.

    \b
      DEVICE to connect with (full device identifier).
      REMOTE path of the file on-device to pull.
      LOCAL directory in which to store the file (optional, defaults to the current directory).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-pull
    """

    command = XrayPullCommand(config, remote, local)
    command.run()


@xray.command()
@click.argument('apk', type=click.Path(exists=True, file_okay=True, readable=True))
@pass_config
def install(config, apk):
    """
    Install an APK to the device.

    \b
      DEVICE to connect with (full device identifier).
      APK to install.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-install
    """

    command = XrayInstallCommand(config, apk)
    command.run()


@xray.command()
@click.argument('package')
@pass_config
def uninstall(config, package):
    """
    Uninstall an app from the device.

    \b
      DEVICE to connect with (full device identifier).
      PACKAGE name to uninstall.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-uninstall
    """

    command = XrayUninstallCommand(config, package)
    command.run()


@xray.command()
@click.option('--port', '-p', help='local port for VNC clients')
@pass_config
def desktop(config, port):
    """
    Open a VNC connection to the device.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-desktop
    """

    command = XrayDesktopCommand(config, port)
    command.run()


@cli.command()
@click.option('--api-key', '--token', '-t',
              help='Your Mason Platform API Key.')
@click.option('--username', '--user', '-u', prompt=True,
              help='Your Mason Platform username.')
@click.option('--password', '--pass', '-p', prompt=True, hide_input=True,
              help='Your Mason Platform password.')
@pass_config
def login(config, api_key, username, password):
    """
    Authenticate via username and password or with an API Key.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-login
    """

    command = LoginCommand(config, api_key, username, password)
    command.run()


@cli.command()
@pass_config
def logout(config):
    """
    Log out of the Mason CLI.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-logout
    """

    command = LogoutCommand(config)
    command.run()


@cli.command(hidden=True)
@pass_config
def version(config):
    """Display the Mason CLI version."""

    command = VersionCommand(config)
    command.run()


if __name__ == '__main__':
    cli()
