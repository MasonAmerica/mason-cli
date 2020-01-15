import logging
import select
import socket
from abc import abstractmethod
from binascii import hexlify

try:
    # noinspection PyCompatibility
    from urllib.parse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import urlparse

from twisted.internet import defer, reactor, protocol, ssl
from twisted.internet.defer import setDebugging
from twisted.logger import globalLogPublisher, STDLibLogObserver, FilteringLogObserver, \
    LogLevelFilterPredicate, \
    LogLevel

import txaio

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
from adb import usb_exceptions

from cli.internal.utils.constants import LOG_PROTOCOL_TRACE

txaio.use_twisted()

MSG_DEVICE_OK = b'device:ok'
MSG_DEVICE_FAIL = b'device:fail'
MSG_CLIENT_OK = b'client:ok'
MSG_CLIENT_FAIL = b'client:fail'


class XRayWebSocketProtocol(WebSocketClientProtocol):

    def forward_message(self, payload):
        self.factory.local_proto.transport.write(payload)

    def onMessage(self, payload, isBinary):
        if self.logger.isEnabledFor(LOG_PROTOCOL_TRACE):
            if isBinary:
                self.logger.debug("[B>>>] %s", hexlify(payload))
            else:
                self.logger.debug("[T>>>] %s", payload)

        if isBinary:
            self.forward_message(payload)
        else:
            if type(payload) == "str":
                payload = payload.encode()
            if payload == MSG_DEVICE_OK:
                self.factory.d.callback(MSG_DEVICE_OK)

    def onClose(self, wasClean, code, reason):
        super(XRayWebSocketProtocol, self).onClose(wasClean, code, reason)
        if code != 1006:
            self.logger.info("Connection closed: [%d] %s", code, reason)

    def sendMessage(self, payload, isBinary=False):
        if self.logger.isEnabledFor(LOG_PROTOCOL_TRACE):
            if isBinary:
                self.logger.debug("[B<<<] %s", hexlify(payload))
            else:
                self.logger.debug("[T<<<] %s", payload)
        super(XRayWebSocketProtocol, self).sendMessage(payload, isBinary)


class XRayWebSocketProtocolFIFO(XRayWebSocketProtocol):
    def forward_message(self, payload):
        self.factory.ssock.send(payload)


class XRayWebSocketFactory(WebSocketClientFactory):
    protocol = XRayWebSocketProtocol

    def __init__(self, logger, *args, **kwargs):
        super(XRayWebSocketFactory, self).__init__(*args, **kwargs)

        self._logger = logger
        self.ws_proto = None
        self.local_proto = None
        self.d = defer.Deferred()

    def buildProtocol(self, addr):
        proto = WebSocketClientFactory.buildProtocol(self, addr)
        proto.factory = self
        proto.logger = self._logger
        self.ws_proto = proto
        return proto

    def clientConnectionFailed(self, connector, reason):
        self._logger.error('Connection failed: %s', reason)
        self.d.errback(reason)

    def clientConnectionLost(self, connector, reason):
        if not self.d.called:
            self._logger.debug('Connection lost: %s', reason)
            self.d.errback(reason)


class XRayWebSocketFactoryFIFO(XRayWebSocketFactory):
    protocol = XRayWebSocketProtocolFIFO

    def __init__(self, logger, *args, **kwargs):
        super(XRayWebSocketFactoryFIFO, self).__init__(logger, *args, **kwargs)

        # use a socketpair as a queue for moving data between the adb client
        # library and the twisted reactor
        self.rsock, self.ssock = socket.socketpair()
        self.rsock.setblocking(0)
        self.rsock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)

    def clientConnectionLost(self, connector, reason):
        self.rsock.shutdown(socket.SHUT_RD)
        self.ssock.shutdown(socket.SHUT_WR)
        if not self.d.called:
            self._logger.debug('Connection lost: %s', reason)
            self.d.errback(reason)


class XRayLocalServerProtocol(protocol.Protocol, object):

    def connectionMade(self):
        self.factory.ws_proto.factory.local_proto = self
        self.factory.ws_proto.sendMessage(MSG_CLIENT_OK)

    def dataReceived(self, data):
        self.factory.ws_proto.sendMessage(data, isBinary=True)

    def connectionLost(self, reason=protocol.connectionDone):
        self.factory.ws_proto.sendMessage(MSG_CLIENT_FAIL)


class XRayLocalServerFactory(protocol.Factory, object):

    def __init__(self, ws_proto, *args, **kwargs):
        self.ws_proto = ws_proto
        self.ws_proto.factory.local_proto = None
        super(XRayLocalServerFactory, self).__init__(*args, **kwargs)

    def buildProtocol(self, addr):
        proto = XRayLocalServerProtocol()
        proto.factory = self
        return proto


class XRayBaseClient(object):

    def __init__(self, logger, url, header=None, **kwargs):
        """X-Ray WebSocket client base class
        Arguments:
          url: The URI of the endpoint where the device is connected

        """
        # if necessary, convert serial to a unicode string
        u = urlparse(url)

        self.host = u.hostname
        if u.port:
            self.port = u.port
        else:
            if u.scheme == "ws":
                self.port = 80
            else:
                self.port = 443

        self.ws_factory = None
        self._logger = logger

        predicate = LogLevelFilterPredicate(LogLevel.error)

        try:
            if logger.isEnabledFor(logging.DEBUG):
                setDebugging(True)
                predicate = LogLevelFilterPredicate(LogLevel.debug)
                if logger.isEnabledFor(LOG_PROTOCOL_TRACE):
                    txaio.set_global_log_level('trace')
                else:
                    txaio.set_global_log_level('debug')
            else:
                txaio.set_global_log_level('info')
        except Exception as exc:
            logger.error(exc)

        globalLogPublisher.addObserver(
            FilteringLogObserver(STDLibLogObserver(name=logger.name), predicates=[predicate]))

        self.ws_factory = self.get_factory(url, header)
        self.ws_factory.d.addErrback(self.close)

        if self.ws_factory.isSecure:
            contextFactory = ssl.ClientContextFactory()
        else:
            contextFactory = None

        def cleanup():
            self.ws_factory.d.cancel()

        reactor.addSystemEventTrigger('after', 'shutdown', cleanup)

        connectWS(self.ws_factory, contextFactory)

    @abstractmethod
    def get_factory(self, url, headers):
        pass

    def close(self, reason):
        reactor.callWhenRunning(reactor.stop)


class XRayProxyServer(XRayBaseClient):

    def __init__(self, logger, url, local_port, **kwargs):
        self.local_port = local_port
        self.local_factory = None

        super(XRayProxyServer, self).__init__(logger, url, **kwargs)

    def run(self):
        reactor.run()

    def get_factory(self, url, headers):
        f = XRayWebSocketFactory(self._logger, url=url, headers=headers)
        f.d.addCallback(self._on_device_ready)
        return f

    def _on_device_ready(self, result):
        self.local_factory = XRayLocalServerFactory(self.ws_factory.ws_proto)
        self._logger.info("X-Ray is connected. Connect a client to localhost:%s", self.local_port)
        reactor.listenTCP(self.local_port, self.local_factory)


class WsHandle(XRayBaseClient):
    """WebSocket connection handle object for python-adb

       We do ugly things to provide a synchronous interface to these Twisted
       components for python-adb. This provides same interface as UsbHandle. """

    def __init__(self, logger, url, timeout_ms=10000, on_connect=None, **kwargs):
        """Initialize the WebSocket Handle.
        Arguments:
          url: The URI of the endpoint where the device is connected

        """
        super(WsHandle, self).__init__(logger, url, **kwargs)

        self._timeout_ms = float(timeout_ms) if timeout_ms else None
        self._serial_number = '%s:%s' % (self.host, self.port)
        self._wst = None
        self._on_running = None

    def run(self, callback):
        self._on_running = callback
        reactor.run()

    def get_factory(self, url, headers):
        f = XRayWebSocketFactoryFIFO(self._logger, url=url, headers=headers)
        f.d.addCallback(self._on_device_ready)
        return f

    def _on_device_ready(self, reason):
        self.ws_factory.ws_proto.sendMessage(MSG_CLIENT_OK)
        reactor.callInThread(self._on_running)

    def _on_close(self, reason):
        if reason is not None:
            raise usb_exceptions.AdbCommandFailureException(reason)

    def _timeout_seconds(self, timeout_ms):
        timeout = self.Timeout(timeout_ms)
        return timeout / 1000.0 if timeout is not None else timeout

    @property
    def serial_number(self):
        return self._serial_number

    def BulkWrite(self, data, timeout=None):
        reactor.callFromThread(self.ws_factory.ws_proto.sendMessage, bytes(data), isBinary=True)

    def BulkRead(self, numbytes, timeout=None):
        t = self._timeout_seconds(timeout)
        buffer = bytearray(numbytes)
        view = memoryview(buffer)
        pos = 0
        while pos < numbytes:
            readable, _, _ = select.select([self.ws_factory.rsock], [], [], t)
            if readable:
                read = self.ws_factory.rsock.recv_into(view[pos:], numbytes - pos, 0)
                if not read:
                    raise usb_exceptions.TcpTimeoutException("Incomplete read!")
                pos += read
            else:
                msg = 'Reading from {} timed out (Timeout {}s)'.format(self._serial_number, t)
                raise usb_exceptions.TcpTimeoutException(msg)
        return bytes(buffer)

    def Timeout(self, timeout_ms):
        return float(timeout_ms) if timeout_ms is not None else self._timeout_ms

    def Close(self, reason=None):
        self.close(reason)
