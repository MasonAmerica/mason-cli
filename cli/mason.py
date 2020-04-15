import os

import click

from cli.config import Config
from cli.config import _manual_atexit_callbacks
from cli.internal.utils.logging import handle_set_level
from cli.internal.utils.logging import install_logger
from cli.internal.utils.mason_types import AliasedGroup
from cli.internal.utils.mason_types import Version

pass_config = click.make_pass_decorator(Config, ensure=True)


# noinspection PyUnusedLocal
def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    config = ctx.ensure_object(Config)
    install_logger(config.logger, 'INFO')

    from cli.internal.commands.version import VersionCommand
    command = VersionCommand(config)
    command.run()

    ctx.exit()


@click.group(cls=AliasedGroup, context_settings={'help_option_names': ['-h', '--help']})
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
@click.option('--verbosity', '-v', expose_value=False, is_eager=True, callback=handle_set_level,
              help='Either CRITICAL, ERROR, WARNING, INFO or DEBUG')
@pass_config
def cli(config, debug, verbose, api_key, id_token, access_token, no_color):
    """
    The Mason CLI provides command line tools to help you manage your configurations in the Mason
    Platform.

    \b
    Full docs: https://docs.bymason.com/cli
    """

    api_key = api_key or os.environ.get('MASON_API_KEY') or os.environ.get('MASON_TOKEN')

    from cli.internal.commands.cli_init import CliInitCommand
    command = CliInitCommand(config, debug, verbose, no_color, api_key, id_token, access_token)
    command.run()


@cli.command()
@pass_config
def init(config):
    """
    Setup a Mason project in the current directory.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-init
    """

    config.skip_verify = False

    from cli.internal.commands.init import InitCommand
    command = InitCommand(config)
    command.run()


@cli.group(cls=AliasedGroup)
@click.option('assume_yes', '-y', '--yes', '--assume-yes', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--dry-run', is_flag=True, default=False,
              help='Show planned operations, but don\'t execute them.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@pass_config
def register(config, assume_yes, dry_run, skip_verify):
    """
    Register artifacts to the Mason Platform.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register
    """

    if skip_verify:
        config.logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or 'CI' in os.environ or skip_verify
    config.execute_ops = not dry_run


@register.command('project')
@click.argument('context', type=click.Path(exists=True, file_okay=False), required=True,
                default='.')
@pass_config
def register_project(config, context):
    """
    Register whole projects.

      CONTEXT pointing the project directory. Defaults to the current directory.

    \b
    Example:
      $ mason register project

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-project
    """

    from cli.internal.commands.register import RegisterProjectCommand
    command = RegisterProjectCommand(config, context)
    command.run()


@register.command('config')
@click.option('--await', 'block', is_flag=True, default=False,
              help='Wait synchronously for the build to finish before continuing.')
@click.option('--turbo/--no-turbo', is_flag=True, default=None, hidden=True,
              help='Enable fast Mason config builds (beta).')
@click.option('--mason-version', hidden=True, help='Pick a specific Mason OS version.')
@click.argument('configs', type=click.Path(exists=True), nargs=-1, required=True)
@pass_config
def register_config(config, block, turbo, mason_version, configs):
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

    if turbo is not None:
        config.logger.warning(
            'The turbo flags are deprecated and will be removed. All builds now use Turbo Builder.')

    from cli.internal.commands.stage import StageCommand
    command = StageCommand(config, configs, block, mason_version)
    command.run()


@register.command('apk')
@click.argument('apks', type=click.Path(exists=True), nargs=-1, required=True)
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

    from cli.internal.commands.register import RegisterApkCommand
    command = RegisterApkCommand(config, apks)
    command.run()


@register.group('media', cls=AliasedGroup)
def register_media():
    """
    Register media artifacts.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-media
    """

    pass


@register_media.command('bootanimation')
@click.argument('name')
@click.argument('version', type=Version())
@click.argument('media', type=click.Path(exists=True, dir_okay=False))
@pass_config
def register_media_bootanimation(config, name, version, media):
    """
    Register boot animation artifacts.

    \b
      NAME of the boot animation.
      VERSION of the boot animation.
      MEDIA file to be uploaded.

    \b
    For example, register a boot animation:
      $ mason register media bootanimation anim-name latest bootanimation.zip

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-media-bootanimation
    """

    from cli.internal.commands.register import RegisterMediaCommand
    command = RegisterMediaCommand(config, name, 'bootanimation', version, media)
    command.run()


@register_media.command('splashscreen')
@click.argument('name')
@click.argument('version', type=Version())
@click.argument('media', type=click.Path(exists=True, dir_okay=False))
@pass_config
def register_media_splash(config, name, version, media):
    """
    Register splash artifacts.

    \b
      NAME of the splash.
      VERSION of the splash.
      MEDIA file to be uploaded.

    \b
    For example, register a splash:
      $ mason register media splash mason-test latest splash.png

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-register-media-splashscreen
    """

    from cli.internal.commands.register import RegisterMediaCommand
    command = RegisterMediaCommand(config, name, 'splash', version, media)
    command.run()


@cli.command(hidden=True)
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

    config.logger.warning('`mason build` is deprecated as '
                          '`mason register config` now starts a build by default.')

    from cli.internal.commands.build import BuildCommand
    command = BuildCommand(config, project, version, block, mason_version)
    command.run()


@cli.command(hidden=True)
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
    config.execute_ops = True

    config.logger.warning('`mason stage` is deprecated, use `mason register config` instead.')

    from cli.internal.commands.stage import StageCommand
    command = StageCommand(config, configs, block, mason_version)
    command.run()


@cli.group(cls=AliasedGroup)
@click.option('assume_yes', '-y', '--yes', '--assume-yes', is_flag=True, default=False,
              help='Don\'t require confirmation.')
@click.option('--dry-run', is_flag=True, default=False,
              help='Show planned operations, but don\'t execute them.')
@click.option('--push', '-p', is_flag=True, default=False,
              help='Push the deployment to devices in the field immediately.')
@click.option('--no-https', is_flag=True, default=False, hidden=True,
              help='Use insecure download links to enable caching via local proxies.')
@click.option('--skip-verify', '-s', is_flag=True, default=False, hidden=True,
              help='Don\'t require confirmation.')
@pass_config
def deploy(config, assume_yes, dry_run, push, no_https, skip_verify):
    """
    Deploy artifacts to groups.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy
    """

    if skip_verify:
        config.logger.warning('--skip-verify is deprecated. Use --assume-yes instead.')

    config.skip_verify = assume_yes or 'CI' in os.environ or skip_verify
    config.execute_ops = not dry_run
    config.push = push
    config.no_https = no_https


@deploy.command('config')
@click.argument('name')
@click.argument('version', type=Version())
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
        version: latest

    \b
    can be deployed to the "development" group with:
      $ mason deploy config mason-test latest development

    \b
    or deployed to multiple groups:
      $ mason deploy config mason-test latest group1 group2 group3

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy-config
    """

    from cli.internal.commands.deploy import DeployConfigCommand
    command = DeployConfigCommand(config, name, version, groups)
    command.run()


@deploy.command('apk')
@click.argument('name')
@click.argument('version', type=Version())
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
    For example, the registered APK "com.test.app"
    can be deployed to the "development" group with:
      $ mason deploy apk com.test.app latest development

    \b
    or deployed to multiple groups:
      $ mason deploy apk com.test.app latest group1 group2 group3

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-deploy-apk
    """

    from cli.internal.commands.deploy import DeployApkCommand
    command = DeployApkCommand(config, name, version, groups)
    command.run()


@deploy.command('ota')
@click.argument('name')
@click.argument('version')
@click.argument('groups', nargs=-1, required=True)
@pass_config
def deploy_ota(config, name, version, groups):
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

    from cli.internal.commands.deploy import DeployOtaCommand
    command = DeployOtaCommand(config, name, version, groups)
    command.run()


@cli.group(invoke_without_command=True, cls=AliasedGroup)
@click.argument('device', required=True, default='')
@pass_config
@click.pass_context
def xray(ctx, config, device):
    """
    Use X-Ray to connect with services on the device.

    \b
      DEVICE to connect with (full device identifier).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray
    """

    if not device:
        config.logger.info(xray.get_help(ctx))
        ctx.exit()
    if not ctx.invoked_subcommand:
        raise click.MissingParameter(param_type='command', ctx=ctx)
    actual_sub_command = xray.get_command(ctx, ctx.invoked_subcommand)
    help_sub_command = xray.get_command(ctx, device)
    if help_sub_command and actual_sub_command.name in ('-h', '--help'):
        config.logger.info(help_sub_command.get_help(ctx))
        ctx.exit()

    config.device = device


@xray.command('-h', hidden=True, add_help_option=False)
@pass_config
@click.pass_context
def xray_help_command_short_form_hack(ctx, config):
    raise click.BadArgumentUsage('No such command "{}".'.format(config.device), ctx=ctx.parent)


@xray.command('--help', hidden=True, add_help_option=False)
@pass_config
@click.pass_context
def xray_help_command_long_form_hack(ctx, config):
    raise click.BadArgumentUsage('No such command "{}".'.format(config.device), ctx=ctx.parent)


@xray.command('logcat', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@pass_config
def xray_logcat(config, args):
    """
    View streaming logs from the device.

    \b
      DEVICE to connect with (full device identifier).
      ARGS supplied to logcat (optional, see https://d.android.com/studio/command-line/logcat).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-logcat
    """

    from cli.internal.commands.xray import XrayLogcatCommand
    command = XrayLogcatCommand(config, args)
    command.run()


@xray.command('shell', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@pass_config
def xray_shell(config, command):
    """
    Open a shell and run commands on the device.

    \b
      DEVICE to connect with (full device identifier).
      COMMAND to run (optional, if empty an interactive shell is opened).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-shell
    """

    from cli.internal.commands.xray import XrayShellCommand
    command = XrayShellCommand(config, command)
    command.run()


@xray.command('push')
@click.argument('local', type=click.Path(exists=True, file_okay=True, readable=True))
@click.argument('remote')
@pass_config
def xray_push(config, local, remote):
    """
    Push files to the device.

    \b
      DEVICE to connect with (full device identifier).
      LOCAL path of the file to be pushed.
      REMOTE path of the destination file.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-push
    """

    from cli.internal.commands.xray import XrayPushCommand
    command = XrayPushCommand(config, local, remote)
    command.run()


@xray.command('pull')
@click.argument('remote')
@click.argument('local', type=click.Path(dir_okay=True), required=False)
@pass_config
def xray_pull(config, remote, local):
    """
    Pull files from the device.

    \b
      DEVICE to connect with (full device identifier).
      REMOTE path of the file on-device to pull.
      LOCAL directory in which to store the file (optional, defaults to the current directory).

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-pull
    """

    from cli.internal.commands.xray import XrayPullCommand
    command = XrayPullCommand(config, remote, local)
    command.run()


@xray.command('install')
@click.argument('apk', type=click.Path(exists=True, file_okay=True, readable=True))
@pass_config
def xray_install(config, apk):
    """
    Install an APK to the device.

    \b
      DEVICE to connect with (full device identifier).
      APK to install.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-install
    """

    from cli.internal.commands.xray import XrayInstallCommand
    command = XrayInstallCommand(config, apk)
    command.run()


@xray.command('uninstall')
@click.argument('package')
@pass_config
def xray_uninstall(config, package):
    """
    Uninstall an app from the device.

    \b
      DEVICE to connect with (full device identifier).
      PACKAGE name to uninstall.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-uninstall
    """

    from cli.internal.commands.xray import XrayUninstallCommand
    command = XrayUninstallCommand(config, package)
    command.run()


@xray.command('desktop', hidden=True)
@click.option('--port', '-p', help='local port for VNC clients')
@pass_config
def xray_desktop(config, port):
    """
    Open a VNC connection to the device.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-desktop
    """

    from cli.internal.commands.xray import XrayDesktopCommand
    command = XrayDesktopCommand(config, port)
    command.run()


@xray.command('adbproxy')
@click.option('--port', '-p', help='local port for ADB clients')
@pass_config
def xray_adbproxy(config, port):
    """
    Open an ADB connection to the device for native client connections.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-adbproxy
    """

    from cli.internal.commands.xray import XrayADBProxyCommand
    command = XrayADBProxyCommand(config, port)
    command.run()


@xray.command('screencap')
@click.option('--outputfile', '-o', help='output filename (automatic if not specified)')
@pass_config
def xray_screencap(config, outputfile):
    """
    Capture a screenshot from the device.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-screencap
    """

    from cli.internal.commands.xray import XrayScreencapCommand
    command = XrayScreencapCommand(config, outputfile)
    command.run()


@xray.command('bugreport')
@pass_config
def xray_bugreport(config):
    """
    Collect a bugreport from the device.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-xray-bugreport
    """

    from cli.internal.commands.xray import XrayBugreportCommand
    command = XrayBugreportCommand(config)
    command.run()


@cli.command()
@click.option('api_key', '-t', '--token', '--api-key',
              help='Your Mason Platform API Key.')
@click.option('username', '-u', '--user', '--username', prompt=True,
              help='Your Mason Platform username.')
@click.option('password', '--pass', '--password', '-p', prompt=True, hide_input=True,
              help='Your Mason Platform password.')
@pass_config
def login(config, api_key, username, password):
    """
    Authenticate via username and password or with an API Key.

    \b
    Full docs: https://docs.bymason.com/mason-cli/#mason-login
    """

    from cli.internal.commands.login import LoginCommand
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

    from cli.internal.commands.logout import LogoutCommand
    command = LogoutCommand(config)
    command.run()


@cli.command(hidden=True)
@pass_config
def version(config):
    """Display the Mason CLI version."""

    from cli.internal.commands.version import VersionCommand
    command = VersionCommand(config)
    command.run()


@cli.command()
@click.argument('command', nargs=-1)
@pass_config
def help(config, command):
    """
    Display help information.

    \b
      COMMAND the name of the command.
    """

    from cli.internal.commands.help import HelpCommand
    command = HelpCommand(config, command)
    command.run()


# noinspection PyUnusedLocal
@cli.resultcallback()
def atexit(*args, **kwargs):
    for (func, args, kwargs) in _manual_atexit_callbacks:
        func(*args, **kwargs)


def main():
    cli()


if __name__ == '__main__':
    main()
