import abc
import os
import posixpath
import traceback

import click
import six
import sys
from adb_shell import constants
from adb_shell.adb_device import AdbDevice
from adb_shell.adb_device import _AdbTransactionInfo
from adb_shell.auth.keygen import keygen

from cli.internal.commands.command import Command
from cli.internal.utils.validation import validate_api_key
from cli.internal.utils.websocket import WSHandleShutdown
from cli.internal.utils.websocket import WsHandle
from cli.internal.utils.websocket import XRayProxyServer

try:
    from adb_shell.auth import sign_cryptography

    RSA_SIGNER = sign_cryptography.CryptographySigner
except ImportError:
    try:
        from adb_shell.auth import sign_pythonrsa

        RSA_SIGNER = sign_pythonrsa.PythonRSASigner.FromRSAKeyPath
    except ImportError:
        try:
            from adb_shell import sign_pycryptodome

            RSA_SIGNER = sign_pycryptodome.PycryptodomeAuthSigner
        except ImportError:
            RSA_SIGNER = None


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

        return list(args)


class XrayLogcatCommand(XrayCommand):
    def __init__(self, config, args):
        super(XrayLogcatCommand, self).__init__(config)
        self.args = args

    @Command.helper('xray logcat')
    def run(self):
        def call():
            self.xray.logcat(self.sanitized_args(self.args))

        self.invoke(call)


class XrayShellCommand(XrayCommand):
    def __init__(self, config, args):
        super(XrayShellCommand, self).__init__(config)
        self.args = args

    @Command.helper('xray shell')
    def run(self):
        def call():
            self.xray.shell(self.sanitized_args(self.args))

        self.invoke(call)


class XrayPushCommand(XrayCommand):
    def __init__(self, config, local, remote):
        super(XrayPushCommand, self).__init__(config)
        self.local = local
        self.remote = remote

    @Command.helper('xray push')
    def run(self):
        def call():
            self.xray.push(self.local, self.remote)

        self.invoke(call)


class XrayPullCommand(XrayCommand):
    def __init__(self, config, remote, local):
        super(XrayPullCommand, self).__init__(config)
        self.remote = remote
        self.local = local

    @Command.helper('xray pull')
    def run(self):
        def call():
            self.xray.pull(self.remote, self.local)

        self.invoke(call)


class XrayInstallCommand(XrayCommand):
    def __init__(self, config, local):
        super(XrayInstallCommand, self).__init__(config)
        self.local = local

    @Command.helper('xray install')
    def run(self):
        def call():
            self.xray.install(self.local)

        self.invoke(call)


class XrayUninstallCommand(XrayCommand):
    def __init__(self, config, package):
        super(XrayUninstallCommand, self).__init__(config)
        self.package = package

    @Command.helper('xray uninstall')
    def run(self):
        def call():
            self.xray.uninstall(self.package)

        self.invoke(call)


class XrayDesktopCommand(XrayCommand):
    def __init__(self, config, port):
        super(XrayDesktopCommand, self).__init__(config)
        self.port = port

    @Command.helper('xray desktop')
    def run(self):
        def call():
            self.xray.desktop(self.port)

        self.invoke(call)


class XRay(object):
    def __init__(self, device, config):
        self._device = device
        self._apikey = config.auth_store['api_key']
        self._progress = None
        self._cur_bytes = 0
        self._url = config.endpoints_store['xray_url'] + "/{}/{}"
        self._logger = config.logger
        self._adbkey = os.path.join(click.get_app_dir('Mason CLI'), 'adbkey')

    def _find_backspace_runs(self, stdout_bytes, start_pos):
        first_backspace_pos = stdout_bytes[start_pos:].find(b'\x08')
        if first_backspace_pos == -1:
            return -1, 0

        end_backspace_pos = (start_pos + first_backspace_pos) + 1
        while True:
            if chr(stdout_bytes[end_backspace_pos]) == '\b':
                end_backspace_pos += 1
            else:
                break

        num_backspaces = end_backspace_pos - (start_pos + first_backspace_pos)

        return (start_pos + first_backspace_pos), num_backspaces

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
        adb = AdbDevice(handle)

        def on_running():
            try:
                signer = RSA_SIGNER(self._adbkey)
                if adb.connect(rsa_keys=[signer], auth_timeout_s=30, timeout_s=10):
                    func(adb, *args, **kwargs)
                    adb.close()
            except WSHandleShutdown:
                return

            except Exception as exc:
                self._logger.error("error bleh: %s" % exc)
                traceback.print_exc()
                raise click.Abort(exc)

        return handle.run(on_running)

    def shell(self, command):
        self._run_in_reactor(self._shell, command)

    def _interactive_shell(
        self,
        device,
        adb_info,
        cmd=None,
        delim=None,
        strip_cmd=True,
        strip_delim=True
    ):
        """
        Retrieves stdout of the current InteractiveShell and sends a shell command if provided.

        Args:
          conn: Instance of AdbConnection
          cmd: Optional. Command to run on the target.
          delim: Optional. Delimiter to look for in the output to know when to stop expecting more
                 output (usually the shell prompt).
        Returns:
          The stdout from the shell command.
        """

        if delim is not None and not isinstance(delim, bytes):
            delim = delim.encode('utf-8')

        # Delimiter may be shell@hammerhead:/ $
        # The user or directory could change, making the delimiter somthing like
        # root@hammerhead:/data/local/tmp $
        # Handle a partial delimiter to search on and clean up
        if delim:
            user_pos = delim.find(b'@')
            dir_pos = delim.rfind(b':/')
            if user_pos != -1 and dir_pos != -1:
                partial_delim = delim[user_pos:dir_pos + 1]  # e.g. @hammerhead:
            else:
                partial_delim = delim

            partial_delim = partial_delim[:-2]

        else:
            partial_delim = None

        try:
            if cmd:
                cmd += '\r'  # Required. Send a carriage return right after the cmd
                cmd = cmd.encode('utf8')

                # Send the cmd raw
                device._write(cmd, adb_info)

                if delim:
                    # Expect multiple WRTE cmds until the delim (usually terminal prompt) is
                    # detected.

                    cmd, data = device._read_until([constants.WRTE], adb_info)
                    if type(data) == bytes:
                        yield data

                    while partial_delim not in data:
                        cmd, data = device._read_until([constants.WRTE], adb_info)
                        yield data

                else:
                    # Otherwise, expect only a single WRTE
                    cmd, data = device._read_until([constants.WRTE], adb_info)

                    # WRTE cmd from device will follow with stdout data
                    yield data

            else:

                # No cmd provided means we should just expect a single line from the terminal.
                # Use this sparingly.
                cmd, data = device._read_until([constants.WRTE, constants.CLSE], adb_info)

                if cmd == b'WRTE':
                    # WRTE cmd from device will follow with stdout data
                    yield data
                else:
                    self._logger.error("Unhandled cmd: {}".format(cmd))

        except Exception as e:
            self._logger.error("InteractiveShell exception (most likely timeout): {}".format(e))
            traceback.print_exc()

    def _shell(self, device, command):
        adb_info = _AdbTransactionInfo(None, None, 10, 20)
        if command:
            if isinstance(command, list):
                command = ' '.join(command)
            output = device._streaming_command(b'shell', command.encode('utf8'), adb_info)
            for line in output:
                sys.stdout.write(line.decode('utf-8'))

        else:
            # Retrieve the initial terminal prompt to use as a delimiter for future reads
            device._open(b'shell:', adb_info)
            terminal_prompt = next(self._interactive_shell(device, adb_info))
            sys.stdout.write(terminal_prompt.decode('utf-8'))

            # Accept user input in a loop and write that into the interactive shells stdin,
            # then print output
            try:
                while True:
                    cmd = input(' ')
                    if not cmd:
                        continue
                    elif cmd == 'exit':
                        break
                    else:
                        output = self._interactive_shell(
                            device, adb_info, cmd, delim=terminal_prompt)
                        for line in output:
                            sys.stdout.write(line.decode('utf-8'))
            except EOFError:
                pass

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
            self._logger.info(output)

    def logcat(self, options=None):
        try:
            self._run_in_reactor(self._logcat, options=options)
        except Exception as exc:
            self._logger.error("logcat error: %s" % exc)

    def _logcat(self, device, options=None):
        if options is None:
            options = []

        self._shell(device, 'logcat %s' % ' '.join(options))

    def push(self, local, remote):
        self._run_in_reactor(self._push, local, remote)

    def _push(self, device, local, remote):
        self._with_progressbar(remote, device.push, local, remote)

    def pull(self, remote, dest_file=None):
        self._run_in_reactor(self._pull, remote, dest_file=dest_file)

    def _pull(self, device, remote, dest_file=None):
        if dest_file is None:
            dest_file = os.path.basename(remote)

        return self._with_progressbar(remote, device.pull, remote, dest_file=str(dest_file))

    def install(self, local_path, replace_existing=True, grant_permissions=False, args=None):
        return self._run_in_reactor(self._install, local_path, args)

    def _install(
        self,
        device,
        local_path,
        replace_existing=True,
        grant_permissions=False,
        args=None
    ):
        destination_dir = '/data/local/tmp/'
        basename = os.path.basename(local_path)
        destination_path = posixpath.join(destination_dir, basename)
        self._push(device, local_path, destination_path)

        cmd = ['pm install']
        if grant_permissions:
            cmd.append('-g')
        if replace_existing:
            cmd.append('-r')
        cmd.append('"{}"'.format(destination_path))

        self._shell(device, cmd)

        # Remove the apk
        rm_cmd = ['rm', destination_path]
        self._shell(device, rm_cmd)

    def uninstall(self, package, keep_data=False, args=None):
        return self._run_in_reactor(self._uninstall, package, keep_data, args)

    def _uninstall(self, device, package, keep_data=False, args=None):
        cmd = ['pm uninstall']
        if keep_data:
            cmd.append('-k')
        cmd.append('"%s"' % package)

        self._shell(device, cmd)
