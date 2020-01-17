import abc
import os
import sys

import click
import six
from adb.adb_commands import AdbCommands
from adb.android_pubkey import keygen

from cli.internal.commands.command import Command
from cli.internal.utils.validation import validate_api_key
from cli.internal.utils.websocket import WsHandle
from cli.internal.utils.websocket import XRayProxyServer

try:
    from adb import sign_cryptography

    rsa_signer = sign_cryptography.CryptographySigner
except ImportError:
    try:
        from adb import sign_pythonrsa

        rsa_signer = sign_pythonrsa.PythonRSASigner.FromRSAKeyPath
    except ImportError:
        try:
            from adb import sign_pycryptodome

            rsa_signer = sign_pycryptodome.PycryptodomeAuthSigner
        except ImportError:
            rsa_signer = None


@six.add_metaclass(abc.ABCMeta)
class XrayCommand(Command):
    def __init__(self, config):
        self.config = config
        self.xray = XRay(config.device, config)

    def invoke(self, method):
        validate_api_key(self.config)

        try:
            method()
        except Exception as exc:
            raise click.Abort(exc)

    @staticmethod
    def sanitized_args(args):
        if args is None:
            return []
        else:
            return list(args)


class XrayLogcatCommand(XrayCommand):
    def __init__(self, config, args):
        super(XrayLogcatCommand, self).__init__(config)
        self.args = args

    def run(self):
        def call():
            self.xray.logcat(self.sanitized_args(self.args))

        self.invoke(call)


class XrayShellCommand(XrayCommand):
    def __init__(self, config, args):
        super(XrayShellCommand, self).__init__(config)
        self.args = args

    def run(self):
        def call():
            self.xray.shell(self.sanitized_args(self.args))

        self.invoke(call)


class XrayPushCommand(XrayCommand):
    def __init__(self, config, local, remote):
        super(XrayPushCommand, self).__init__(config)
        self.local = local
        self.remote = remote

    def run(self):
        def call():
            self.xray.push(self.local, self.remote)

        self.invoke(call)


class XrayPullCommand(XrayCommand):
    def __init__(self, config, remote, local):
        super(XrayPullCommand, self).__init__(config)
        self.remote = remote
        self.local = local

    def run(self):
        def call():
            self.xray.pull(self.remote, self.local)

        self.invoke(call)


class XrayInstallCommand(XrayCommand):
    def __init__(self, config, local):
        super(XrayInstallCommand, self).__init__(config)
        self.local = local

    def run(self):
        def call():
            self.xray.install(self.local)

        self.invoke(call)


class XrayUninstallCommand(XrayCommand):
    def __init__(self, config, package):
        super(XrayUninstallCommand, self).__init__(config)
        self.package = package

    def run(self):
        def call():
            self.xray.uninstall(self.package)

        self.invoke(call)


class XrayDesktopCommand(XrayCommand):
    def __init__(self, config, port):
        super(XrayDesktopCommand, self).__init__(config)
        self.port = port

    def run(self):
        def call():
            self.xray.desktop(self.port)

        self.invoke(call)


class XRay(object):
    def __init__(self, device, config):
        self._device = device
        self._apikey = config.auth_store['api_key']
        self._adb = AdbCommands()
        self._progress = None
        self._cur_bytes = 0
        self._url = config.endpoints_store['xray_url'] + "/{}/{}"
        self._logger = config.logger
        self._adbkey = os.path.join(click.get_app_dir('Mason CLI'), 'adbkey')

    def _get_url(self, service):
        return self._url.format(self._device, service)

    def _keygen(self):
        try:
            keygen(self._adbkey)
        except Exception as exc:
            self._logger.error(exc)

    def _connect_adb(self):
        if not os.path.isfile(self._adbkey):
            self._keygen()

        auth = {'Authorization': 'Basic {}'.format(self._apikey)}
        return WsHandle(self._logger, self._get_url('adb'), timeout_ms=5000, header=auth)

    def desktop(self, port=None):
        if port is None:
            port = 5558

        auth = {'Authorization': 'Basic {}'.format(self._apikey)}
        XRayProxyServer(self._logger, self._get_url('vnc'), port, timeout_ms=5000,
                        header=auth).run()

    def _run_in_reactor(self, func, *args, **kwargs):
        handle = self._connect_adb()

        def on_running():
            try:
                signer = rsa_signer(self._adbkey)
                device = self._adb.ConnectDevice(handle=handle, rsa_keys=[signer],
                                                 auth_timeout_ms=30000)
                if device is not None:
                    try:
                        func(device, *args, **kwargs)
                    except Exception:
                        pass
                    device.Close()
            except Exception as exc:
                self._logger.error("error: %s" % exc)
                raise click.Abort(exc)

        return handle.run(on_running)

    def logcat(self, options=None):
        self._run_in_reactor(self._logcat, options=options)

    def _logcat(self, device, options=None):
        if options is None:
            options = []

        output = device.Logcat(' '.join(options))
        for line in output:
            sys.stdout.write(line)

    def shell(self, command):
        self._run_in_reactor(self._shell, command)

    def _shell(self, device, command):
        if command:
            output = device.StreamingShell(' '.join(command))
            for line in output:
                sys.stdout.write(line)
        else:
            # Retrieve the initial terminal prompt to use as a delimiter for future reads
            terminal_prompt = device.InteractiveShell()
            sys.stdout.write(terminal_prompt.decode('utf-8'))

            # Accept user input in a loop and write that into the interactive shells stdin,
            # then print output
            while True:
                cmd = input(' ')
                if not cmd:
                    continue
                elif cmd == 'exit':
                    break
                else:
                    stdout = device.InteractiveShell(
                        cmd, strip_cmd=True, delim=terminal_prompt, strip_delim=False)
                    if stdout:
                        if isinstance(stdout, bytes):
                            stdout = stdout.decode('utf-8')
                            sys.stdout.write(stdout)

    def _with_progressbar(self, label, func, *args, **kwargs):
        with click.progressbar(length=0, label=label) as progress:
            progress.length_known = False

            def callback(filename, bytes_written, total_bytes):
                if not progress.length_known:
                    progress.length = total_bytes
                    progress.length_known = True
                progress.update(bytes_written - self._cur_bytes)
                self._cur_bytes = bytes_written

            output = func(progress_callback=callback, *args, **kwargs)
            self._logger.info("".join(output))

    def push(self, local, remote):
        self._run_in_reactor(self._push, local, remote)

    def _push(self, device, local, remote):
        self._with_progressbar(remote, device.Push, local, remote)

    def pull(self, remote, dest_file=None):
        return self._run_in_reactor(self._pull, remote, dest_file=dest_file)

    def _pull(self, device, remote, dest_file=None):
        if dest_file is None:
            dest_file = os.path.basename(remote)

        return self._with_progressbar(remote, device.Pull, remote, dest_file=str(dest_file))

    def install(self, local_path, args=None):
        return self._run_in_reactor(self._install, local_path, args)

    def _install(self, device, local_path, args=None):
        def wrapped(progress_callback=None, *args, **kwargs):
            return device.Install(transfer_progress_callback=progress_callback, *args, **kwargs)

        return self._with_progressbar(local_path, wrapped, local_path)

    def uninstall(self, package, args=None):
        return self._run_in_reactor(self._uninstall, package, args)

    def _uninstall(self, device, package, args=None):
        self._logger.info(device.Uninstall(package))
