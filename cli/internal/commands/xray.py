# pylint: disable=protected-access
import abc
import os
import posixpath
import socket
import sys
import threading
from time import gmtime
from time import strftime

import click
import six
from adb_shell import constants
from adb_shell.adb_device import AdbDevice
from adb_shell.adb_device import _AdbTransactionInfo
from adb_shell.adb_message import AdbMessage
from adb_shell.auth.keygen import keygen
from adb_shell.exceptions import AdbCommandFailureException
from adb_shell.exceptions import PushFailedError
from adb_shell.exceptions import TcpTimeoutException

from cli.config import Config
from cli.internal.utils.remote import build_url

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

from cli.internal.commands.command import Command
from cli.internal.utils.validation import validate_api_key
from cli.internal.utils.websocket import WSHandleShutdown
from cli.internal.utils.websocket import WsHandle
from cli.internal.utils.websocket import XRayProxyServer


@six.add_metaclass(abc.ABCMeta)
class XrayCommand(Command):
    def __init__(self, config: Config):
        super(XrayCommand, self).__init__(config)
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
    def __init__(self, config: Config, args):
        super(XrayLogcatCommand, self).__init__(config)
        self.args = args

    @Command.helper('xray logcat')
    def run(self):
        def call():
            self.xray.logcat(self.sanitized_args(self.args))

        self.invoke(call)


class XrayShellCommand(XrayCommand):
    def __init__(self, config: Config, args):
        super(XrayShellCommand, self).__init__(config)
        self.args = args

    @Command.helper('xray shell')
    def run(self):
        def call():
            self.xray.shell(self.sanitized_args(self.args))

        self.invoke(call)


class XrayPushCommand(XrayCommand):
    def __init__(self, config: Config, local, remote):
        super(XrayPushCommand, self).__init__(config)
        self.local = local
        self.remote = remote

    @Command.helper('xray push')
    def run(self):
        def call():
            self.xray.push(self.local, self.remote)

        self.invoke(call)


class XrayPullCommand(XrayCommand):
    def __init__(self, config: Config, remote, local):
        super(XrayPullCommand, self).__init__(config)
        self.remote = remote
        self.local = local

    @Command.helper('xray pull')
    def run(self):
        def call():
            self.xray.pull(self.remote, self.local)

        self.invoke(call)


class XrayInstallCommand(XrayCommand):
    def __init__(self, config: Config, local):
        super(XrayInstallCommand, self).__init__(config)
        self.local = local

    @Command.helper('xray install')
    def run(self):
        def call():
            self.xray.install(self.local)

        self.invoke(call)


class XrayUninstallCommand(XrayCommand):
    def __init__(self, config: Config, package):
        super(XrayUninstallCommand, self).__init__(config)
        self.package = package

    @Command.helper('xray uninstall')
    def run(self):
        def call():
            self.xray.uninstall(self.package)

        self.invoke(call)


class XrayDesktopCommand(XrayCommand):
    def __init__(self, config: Config, port):
        super(XrayDesktopCommand, self).__init__(config)
        self.port = port

    @Command.helper('xray desktop')
    def run(self):
        def call():
            self.xray.desktop(self.port)

        self.invoke(call)


class XrayADBProxyCommand(XrayCommand):
    def __init__(self, config: Config, port):
        super(XrayADBProxyCommand, self).__init__(config)
        self.port = port

    @Command.helper('xray adbproxy')
    def run(self):
        def call():
            self.xray.adbproxy(self.port)

        self.invoke(call)


class XrayScreencapCommand(XrayCommand):
    def __init__(self, config: Config, outputfile):
        super(XrayScreencapCommand, self).__init__(config)
        self.outputfile = outputfile

    @Command.helper('xray screencap')
    def run(self):
        def call():
            self.xray.screencap(self.outputfile)

        self.invoke(call)


class XrayBugreportCommand(XrayCommand):
    def __init__(self, config: Config):
        super(XrayBugreportCommand, self).__init__(config)

    @Command.helper('xray bugreport')
    def run(self):
        def call():
            self.xray.bugreport()

        self.invoke(call)


class XRay(object):
    def __init__(self, device, config: Config):
        self._device = device
        self._auth = {'Authorization': 'Basic {}'.format(config.auth_store['api_key'])}
        self._progress = None
        self._cur_bytes = 0
        self._url = build_url(config.endpoints_store, 'xray_url') + "/{}/{}"
        self._logger = config.logger
        self._adbkey = os.path.join(click.get_app_dir('Mason CLI'), 'adbkey')
        self._awaiting_auth = False

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

        return WsHandle(self._logger, self._get_url('adb'), timeout_ms=5000, header=self._auth)

    def _is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def adbproxy(self, port=None):
        if port is None:
            port = 5555
        port = int(port)

        if self._is_port_in_use(port):
            self._logger.error("Port %s is in use, please select a different local port." % port)
            return

        XRayProxyServer(self._logger, self._get_url('adb'), port, timeout_ms=5000,
                        header=self._auth).run()

    def desktop(self, port=None):
        if port is None:
            port = 5558
        port = int(port)

        if self._is_port_in_use(port):
            self._logger.error("Port %s is in use, please select a different local port." % port)
            return

        XRayProxyServer(self._logger, self._get_url('vnc'), port, timeout_ms=5000,
                        header=self._auth).run()

    def _run_in_reactor(self, func, *args, **kwargs):
        handle = self._connect_adb()
        adb = AdbDevice(handle)

        def auth_cb(device):
            self._awaiting_auth = True
            self._logger.info("Waiting for connection to be accepted on the device..")

        def on_running():
            try:
                signer = RSA_SIGNER(self._adbkey)
                if adb.connect(rsa_keys=[signer], auth_timeout_s=30,
                               timeout_s=10, auth_callback=auth_cb):
                    func(adb, *args, **kwargs)

            except WSHandleShutdown:
                pass

            except TcpTimeoutException:
                if self._awaiting_auth:
                    self._logger.error("Connection was not accepted on the device "
                                       "within 30 seconds.")
                else:
                    self._logger.error("Connection to the device timed out")

            except Exception as exc:
                self._logger.debug(exc, exc_info=True)
                if len(exc.args) >= 1 and type(exc.args[0]) is bytearray:
                    self._logger.error(exc.args[0].decode('utf-8'))
                else:
                    self._logger.error(exc)

            finally:
                adb.close()

        return handle.run(on_running)

    def shell(self, command):
        self._run_in_reactor(self._shell, command)

    def _interactive_shell(self, device):
        adb_info = _AdbTransactionInfo(None, None, 600, 20)

        device._open(b'shell:', adb_info)

        def writer():
            while True:
                try:
                    cmd = input()
                    cmd += '\r'  # Required. Send a carriage return right after the cmd
                    cmd = cmd.encode('utf8')

                    # Send the cmd raw
                    msg = AdbMessage(constants.WRTE, adb_info.local_id, adb_info.remote_id, cmd)
                    device._send(msg, adb_info)
                except EOFError:
                    device.close()
                    break

        input_thread = threading.Thread(target=writer)
        input_thread.daemon = True
        input_thread.start()

        while True:
            try:
                _, data = device._read_until([constants.OKAY, constants.WRTE,
                                              constants.CLSE], adb_info)
                if isinstance(data, bytes):
                    sys.stdout.write(data.decode('utf-8'))
                    sys.stdout.flush()
            except TcpTimeoutException:
                pass
            except WSHandleShutdown:
                break

    def _noninteractive_shell(self, device, command, timeout_s=600, total_timeout_s=20):
        adb_info = _AdbTransactionInfo(None, None, timeout_s, total_timeout_s)

        if isinstance(command, list):
            command = ' '.join(command)
        return device._streaming_command(b'shell', command.encode('utf8'), adb_info)

    def _shell(self, device, command):
        if command:
            output = self._noninteractive_shell(device, command)
            for line in output:
                sys.stdout.write(line.decode('utf-8'))
        else:
            self._interactive_shell(device)

    def _with_progressbar(self, label, func, *args, **kwargs):
        with click.progressbar(length=0, label=label) as progress:
            progress.length_known = False

            def callback(filename, bytes_written, total_bytes):
                if not progress.length_known:
                    progress.length = total_bytes
                    progress.length_known = True
                progress.update(bytes_written - self._cur_bytes)
                self._cur_bytes = bytes_written

            return func(progress_callback=callback, *args, **kwargs)

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
        if remote.endswith("/"):
            remote += os.path.basename(local)
        self._run_in_reactor(self._push, local, remote)

    def _push(self, device, local, remote):
        try:
            self._with_progressbar(remote, device.push, local, remote)
        except PushFailedError as e:
            if not remote.startswith('/') and 'No such file or directory' in str(e):
                remote = '/sdcard/' + remote
                self._with_progressbar(remote, device.push, local, remote)
            else:
                raise e

    def pull(self, remote, dest_file=None):
        self._run_in_reactor(self._pull, remote, dest_file=dest_file)

    def _pull(self, device, remote, dest_file=None):
        if dest_file is None:
            dest_file = os.path.basename(remote)

        try:
            return self._with_progressbar(remote, device.pull, remote, dest_file=str(dest_file))
        except AdbCommandFailureException as e:
            if not remote.startswith('/') and 'No such file or directory' in str(e):
                remote = '/sdcard/' + remote
                return self._with_progressbar(remote, device.pull, remote, dest_file=str(dest_file))
            else:
                raise e

    def install(self, local_path, replace_existing=True, grant_permissions=False, args=None):

        if not os.path.exists(local_path):
            self._logger.error("File does not exist: %s" % local_path)
            return

        if not local_path.endswith('.apk'):
            self._logger.error("Only .apk files may be installed")
            return

        return self._run_in_reactor(self._install, local_path,
                                    replace_existing=replace_existing,
                                    grant_permissions=grant_permissions)

    def _install(self, device, local_path, replace_existing=True, grant_permissions=False):
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

    def screencap(self, outputfile=None):
        return self._run_in_reactor(self._screencap, outputfile)

    def _screencap(self, device, outputfile=None):
        if outputfile is None:
            outputfile = "screencap-%s-%s.png" % (self._device, strftime("%Y%m%d%H%M%S", gmtime()))

        rpath = "/data/local/tmp/%s" % outputfile
        self._shell(device, ['/system/bin/screencap', '-p', rpath])
        self._pull(device, rpath)
        self._shell(device, ['rm', rpath])

        self._logger.info("Screen captured to %s" % outputfile)

    def _bugreport(self, device):
        self._logger.info("Collecting bugreport, this may take a minute..")
        output = self._noninteractive_shell(device, ['/system/bin/bugreportz'], timeout_s=300)
        zpath = None
        for line in output:
            if isinstance(line, bytes):
                data = line.decode('utf-8').strip()
                if data.startswith("OK:"):
                    zpath = data.split(":")[1]

        if zpath is None:
            self._logger.error("Failed to capture bug report!")
            return

        self._pull(device, zpath)
        self._logger.info("Bug report saved to %s" % os.path.basename(zpath))

    def bugreport(self):
        return self._run_in_reactor(self._bugreport)
