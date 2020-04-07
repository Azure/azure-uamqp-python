"""Transport implementation."""
# pylint: skip-file
# Copyright (C) 2009 Barry Pederson <bp@barryp.org>

import asyncio
import errno
import re
import socket
import ssl
import struct
from ssl import SSLError
from contextlib import contextmanager
from io import BytesIO
import logging
from threading import Lock

import certifi

from .._platform import KNOWN_TCP_OPTS, SOL_TCP, pack, unpack
from .._encode import encode_frame
from .._decode import decode_frame, decode_empty_frame, decode_pickle_frame, construct_frame
from ..performatives import HeaderFrame, TLSHeaderFrame
from .._transport import (
    unpack_frame_header,
    decode_response,
    get_errno,
    to_host_port,
    DEFAULT_SOCKET_SETTINGS,
    IPV6_LITERAL,
    SIGNED_INT_MAX,
    _UNAVAIL,
    set_cloexec
)


_LOGGER = logging.getLogger(__name__)


class _AsyncAbstractTransport(object):
    """Common superclass for TCP and SSL transports."""

    def __init__(self, host, connect_timeout=None,
                 read_timeout=None, write_timeout=None,
                 socket_settings=None, raise_on_initial_eintr=True, **kwargs):
        self.connected = False
        self.sock = None
        self.raise_on_initial_eintr = raise_on_initial_eintr
        self._read_buffer = BytesIO()
        self.host, self.port = to_host_port(host)
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.socket_settings = socket_settings
        self.socket_lock = asyncio.Lock()
        self.loop = asyncio.get_running_loop()

    async def connect(self):
        try:
            # are we already connected?
            if self.connected:
                return
            await self._connect(self.host, self.port, self.connect_timeout)
            self._init_socket(
                self.socket_settings, self.read_timeout, self.write_timeout,
            )
            # we've sent the banner; signal connect
            # EINTR, EAGAIN, EWOULDBLOCK would signal that the banner
            # has _not_ been sent
            self.connected = True
        except (OSError, IOError, SSLError):
            # if not fully connected, close socket, and reraise error
            if self.sock and not self.connected:
                self.sock.close()
                self.sock = None
            raise

    @contextmanager
    def block_with_timeout(self, timeout):
        if timeout is None:
            yield self.sock
        else:
            sock = self.sock
            prev = sock.gettimeout()
            if prev != timeout:
                sock.settimeout(timeout)
            try:
                yield self.sock
            except SSLError as exc:
                if 'timed out' in str(exc):
                    # http://bugs.python.org/issue10272
                    raise socket.timeout()
                elif 'The operation did not complete' in str(exc):
                    # Non-blocking SSL sockets can throw SSLError
                    raise socket.timeout()
                raise
            except socket.error as exc:
                if get_errno(exc) == errno.EWOULDBLOCK:
                    raise socket.timeout()
                raise
            finally:
                if timeout != prev:
                    sock.settimeout(prev)

    @contextmanager
    def block(self):
        bocking_timeout = None
        sock = self.sock
        prev = sock.gettimeout()
        if prev != bocking_timeout:
            sock.settimeout(bocking_timeout)
        try:
            yield self.sock
        except SSLError as exc:
            if 'timed out' in str(exc):
                # http://bugs.python.org/issue10272
                raise socket.timeout()
            elif 'The operation did not complete' in str(exc):
                # Non-blocking SSL sockets can throw SSLError
                raise socket.timeout()
            raise
        except socket.error as exc:
            if get_errno(exc) == errno.EWOULDBLOCK:
                raise socket.timeout()
            raise
        finally:
            if bocking_timeout != prev:
                sock.settimeout(prev)

    async def _connect(self, host, port, timeout):
        # Below we are trying to avoid additional DNS requests for AAAA if A
        # succeeds. This helps a lot in case when a hostname has an IPv4 entry
        # in /etc/hosts but not IPv6. Without the (arguably somewhat twisted)
        # logic below, getaddrinfo would attempt to resolve the hostname for
        # both IP versions, which would make the resolver talk to configured
        # DNS servers. If those servers are for some reason not available
        # during resolution attempt (either because of system misconfiguration,
        # or network connectivity problem), resolution process locks the
        # _connect call for extended time.
        addr_types = (socket.AF_INET, socket.AF_INET6)
        addr_types_num = len(addr_types)
        for n, family in enumerate(addr_types):
            # first, resolve the address for a single address family
            try:
                entries = await self.loop.getaddrinfo(
                    host, port, family=family, type=socket.SOCK_STREAM, proto=SOL_TCP)
                entries_num = len(entries)
            except socket.gaierror:
                # we may have depleted all our options
                if n + 1 >= addr_types_num:
                    # if getaddrinfo succeeded before for another address
                    # family, reraise the previous socket.error since it's more
                    # relevant to users
                    raise (e
                           if e is not None
                           else socket.error(
                               "failed to resolve broker hostname"))
                continue  # pragma: no cover

            # now that we have address(es) for the hostname, connect to broker
            for i, res in enumerate(entries):
                af, socktype, proto, _, sa = res
                try:
                    self.sock = socket.socket(af, socktype, proto)
                    try:
                        set_cloexec(self.sock, True)
                    except NotImplementedError:
                        pass
                    self.sock.settimeout(timeout)
                    await self.loop.sock_connect(self.sock, sa)
                except socket.error as ex:
                    e = ex
                    if self.sock is not None:
                        self.sock.close()
                        self.sock = None
                    # we may have depleted all our options
                    if i + 1 >= entries_num and n + 1 >= addr_types_num:
                        raise
                else:
                    # hurray, we established connection
                    return

    def _init_socket(self, socket_settings, read_timeout, write_timeout):
        self.sock.settimeout(None)  # set socket back to blocking mode
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._set_socket_options(socket_settings)

        # set socket timeouts
        # for timeout, interval in ((socket.SO_SNDTIMEO, write_timeout),
        #                           (socket.SO_RCVTIMEO, read_timeout)):
        #     if interval is not None:
        #         sec = int(interval)
        #         usec = int((interval - sec) * 1000000)
        #         self.sock.setsockopt(
        #             socket.SOL_SOCKET, timeout,
        #             pack('ll', sec, usec),
        #         )
        self._setup_transport()
        self.sock.settimeout(0.1)  # set socket back to non-blocking mode

    def _get_tcp_socket_defaults(self, sock):
        tcp_opts = {}
        for opt in KNOWN_TCP_OPTS:
            enum = None
            if opt == 'TCP_USER_TIMEOUT':
                try:
                    from socket import TCP_USER_TIMEOUT as enum
                except ImportError:
                    # should be in Python 3.6+ on Linux.
                    enum = 18
            elif hasattr(socket, opt):
                enum = getattr(socket, opt)

            if enum:
                if opt in DEFAULT_SOCKET_SETTINGS:
                    tcp_opts[enum] = DEFAULT_SOCKET_SETTINGS[opt]
                elif hasattr(socket, opt):
                    tcp_opts[enum] = sock.getsockopt(
                        SOL_TCP, getattr(socket, opt))
        return tcp_opts

    def _set_socket_options(self, socket_settings):
        tcp_opts = self._get_tcp_socket_defaults(self.sock)
        if socket_settings:
            tcp_opts.update(socket_settings)
        for opt, val in tcp_opts.items():
            self.sock.setsockopt(SOL_TCP, opt, val)

    async def _read(self, n, initial=False):
        """Read exactly n bytes from the peer."""
        raise NotImplementedError('Must be overriden in subclass')

    def _setup_transport(self):
        """Do any additional initialization of the class."""
        pass

    def _shutdown_transport(self):
        """Do any preliminary work in shutting down the connection."""
        pass

    async def _write(self, s):
        """Completely write a string to the peer."""
        raise NotImplementedError('Must be overriden in subclass')

    def close(self):
        if self.sock is not None:
            self._shutdown_transport()
            # Call shutdown first to make sure that pending messages
            # reach the AMQP broker if the program exits after
            # calling this method.
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None
        self.connected = False

    async def read(self, unpack=unpack_frame_header, verify_frame_type=0, **kwargs):  # TODO: verify frame type?
        read_frame_buffer = BytesIO()
        try:
            frame_header = await self._read(8, initial=True)
            read_frame_buffer.write(frame_header)
            size, offset, frame_type, channel = unpack(frame_header)
            if not size:
                return frame_header, channel, None  # Empty frame or header

            # >I is an unsigned int, but the argument to sock.recv is signed,
            # so we know the size can be at most 2 * SIGNED_INT_MAX
            payload_size = size - len(frame_header)
            payload = memoryview(bytearray(payload_size))
            if size > SIGNED_INT_MAX:
                read_frame_buffer.write(await self._read(SIGNED_INT_MAX, buffer=payload))
                read_frame_buffer.write(await self._read(size - SIGNED_INT_MAX, buffer=payload[SIGNED_INT_MAX:]))
            else:
                read_frame_buffer.write(await self._read(payload_size, buffer=payload))
        except socket.timeout:
            read_frame_buffer.write(self._read_buffer.getvalue())
            self._read_buffer = read_frame_buffer
            self._read_buffer.seek(0)
            raise
        except (OSError, IOError, SSLError, socket.error) as exc:
            # Don't disconnect for ssl read time outs
            # http://bugs.python.org/issue10272
            if isinstance(exc, SSLError) and 'timed out' in str(exc):
                raise socket.timeout()
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise
        offset -= 2
        return frame_header, channel, payload[offset:]

    async def write(self, s):
        try:
            await self._write(s)
        except socket.timeout:
            raise
        except (OSError, IOError, socket.error) as exc:
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise

    async def receive_frame(self, *args, **kwargs):
        try:
            header, channel, payload = await self.read(**kwargs) 
            if not payload:
                decoded = decode_empty_frame(header)
            else:
                decoded = decode_frame(payload)
            # TODO: Catch decode error and return amqp:decode-error
            _LOGGER.info("ICH%d <- %r", channel, decoded)
            return channel, decoded
        except socket.timeout:
            return None, None

    async def receive_frame_with_lock(self, *args, **kwargs):
        try:
            async with self.socket_lock:
                header, channel, payload = await self.read(**kwargs) 
            if not payload:
                decoded = decode_empty_frame(header)
            else:
                decoded = decode_frame(payload)
            return channel, decoded
        except socket.timeout:
            return None, None

    def receive_frame_batch(self, batch, **kwargs):
        #if self.thread_pool:
        #    return self.thread_pool.map(self.receive_frame_with_lock, range(batch))
        frames = []
        while len(frames) < batch:
            try:
                header, channel, payload = self.read(**kwargs) 
                frames.append((header.tobytes(), channel, payload.tobytes()))
            except socket.timeout:
                break
        if self.thread_pool:
            return (construct_frame(*f) for f in self.thread_pool.map(decode_proc_response, frames, chunksize=10))
        else:
            return (decode_response(f) for f in frames)

    async def send_frame(self, channel, frame, **kwargs):
        header, performative = encode_frame(frame, **kwargs)
        if performative is None:
            data = header
        else:
            encoded_channel = struct.pack('>H', channel)
            data = header + encoded_channel + performative

        await self.write(data)
        _LOGGER.info("OCH%d -> %r", channel, frame)

    async def negotiate(self, encode, decode):
        pass


class SSLTransport(_AsyncAbstractTransport):
    """Transport that works over SSL."""

    def __init__(self, host, connect_timeout=None, ssl=None, **kwargs):
        self.sslopts = ssl if isinstance(ssl, dict) else {}
        super(SSLTransport, self).__init__(
            host, connect_timeout=connect_timeout, **kwargs)

    def _setup_transport(self):
        """Wrap the socket in an SSL object."""
        self.sock = self._wrap_socket(self.sock, **self.sslopts)
        a = self.sock.do_handshake()

    def _wrap_socket(self, sock, context=None, **sslopts):
        if context:
            return self._wrap_context(sock, sslopts, **context)
        return self._wrap_socket_sni(sock, **sslopts)

    def _wrap_context(self, sock, sslopts, check_hostname=None, **ctx_options):
        ctx = ssl.create_default_context(**ctx_options)
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_verify_locations(cafile=certifi.where())
        ctx.check_hostname = check_hostname
        return ctx.wrap_socket(sock, **sslopts)

    def _wrap_socket_sni(self, sock, keyfile=None, certfile=None,
                         server_side=False, cert_reqs=ssl.CERT_REQUIRED,
                         ca_certs=None, do_handshake_on_connect=False,
                         suppress_ragged_eofs=True, server_hostname=None,
                         ciphers=None, ssl_version=None):
        """Socket wrap with SNI headers.

        Default `ssl.wrap_socket` method augmented with support for
        setting the server_hostname field required for SNI hostname header
        """
        # Setup the right SSL version; default to optimal versions across
        # ssl implementations
        if ssl_version is None:
            # older versions of python 2.7 and python 2.6 do not have the
            # ssl.PROTOCOL_TLS defined the equivalent is ssl.PROTOCOL_SSLv23
            # we default to PROTOCOL_TLS and fallback to PROTOCOL_SSLv23
            # TODO: Drop this once we drop Python 2.7 support
            if hasattr(ssl, 'PROTOCOL_TLS'):
                ssl_version = ssl.PROTOCOL_TLS
            else:
                ssl_version = ssl.PROTOCOL_SSLv23

        opts = {
            'sock': sock,
            'keyfile': keyfile,
            'certfile': certfile,
            'server_side': server_side,
            'cert_reqs': cert_reqs,
            'ca_certs': ca_certs,
            'do_handshake_on_connect': do_handshake_on_connect,
            'suppress_ragged_eofs': suppress_ragged_eofs,
            'ciphers': ciphers,
            #'ssl_version': ssl_version
        }

        sock = ssl.wrap_socket(**opts)
        # Set SNI headers if supported
        if (server_hostname is not None) and (
                hasattr(ssl, 'HAS_SNI') and ssl.HAS_SNI) and (
                hasattr(ssl, 'SSLContext')):
            context = ssl.SSLContext(opts['ssl_version'])
            context.verify_mode = cert_reqs
            if cert_reqs != ssl.CERT_NONE:
                context.check_hostname = True
            if (certfile is not None) and (keyfile is not None):
                context.load_cert_chain(certfile, keyfile)
            sock = context.wrap_socket(sock, server_hostname=server_hostname)
        return sock

    def _shutdown_transport(self):
        """Unwrap a SSL socket, so we can call shutdown()."""
        if self.sock is not None:
            try:
                self.sock = self.sock.unwrap()
            except OSError:
                pass

    async def _read(self, toread, initial=False, buffer=None,
              _errnos=(errno.ENOENT, errno.EAGAIN, errno.EINTR)):
        # According to SSL_read(3), it can at most return 16kb of data.
        # Thus, we use an internal read buffer like TCPTransport._read
        # to get the exact number of bytes wanted.
        length = 0
        view = buffer or memoryview(bytearray(toread))
        nbytes = self._read_buffer.readinto(view)
        toread -= nbytes
        length += nbytes
        try:
            while toread:
                try:
                    nbytes = await self.loop.sock_recv_into(self.sock, view[nbytes:])
                except socket.error as exc:
                    # ssl.sock.read may cause a SSLerror without errno
                    # http://bugs.python.org/issue10272
                    if isinstance(exc, SSLError) and 'timed out' in str(exc):
                        raise socket.timeout()
                    # ssl.sock.read may cause ENOENT if the
                    # operation couldn't be performed (Issue celery#1414).
                    if exc.errno in _errnos:
                        if initial and self.raise_on_initial_eintr:
                            raise socket.timeout()
                        continue
                    raise
                if not nbytes:
                    raise IOError('Server unexpectedly closed connection')

                length += nbytes
                toread -= nbytes
        except:  # noqa
            self._read_buffer = BytesIO(view[:length])
            raise
        return view

    async def _write(self, s):
        """Write a string out to the SSL socket fully."""
        await self.loop.sock_sendall(self.sock, s)

    async def negotiate(self):
        with self.block():
            await self.send_frame(0, TLSHeaderFrame())
            channel, returned_header = await self.receive_frame(verify_frame_type=None)
            if not isinstance(returned_header, TLSHeaderFrame):
                raise ValueError("Mismatching TLS header protocol. Excpected code: {}, received code: {}".format(
                    TLSHeaderFrame._code, returned_header._code))


class AsyncTCPTransport(_AsyncAbstractTransport):
    """Transport that deals directly with TCP socket."""

    async def _read(self, n, initial=False, _errnos=(errno.EAGAIN, errno.EINTR)):
        """Read exactly n bytes from the socket."""
        rbuf = self._read_buffer
        try:
            while len(rbuf) < n:
                try:
                    s = await self.loop.sock_recv(self.sock, n - len(rbuf))
                except socket.error as exc:
                    if exc.errno in _errnos:
                        if initial and self.raise_on_initial_eintr:
                            raise socket.timeout()
                        continue
                    raise
                if not s:
                    raise IOError('Server unexpectedly closed connection')
                rbuf += s
        except:  # noqa
            self._read_buffer = rbuf
            raise

        result, self._read_buffer = rbuf[:n], rbuf[n:]
        return result
    
    async def _write(self, s):
        await self.loop.sock_sendall(self.sock, s)


def AsyncTransport(host, connect_timeout=None, ssl=False, **kwargs):
    """Create transport.

    Given a few parameters from the Connection constructor,
    select and create a subclass of _AsyncAbstractTransport.
    """
    transport = AsyncSSLTransport if ssl else AsyncTCPTransport
    return transport(host, connect_timeout=connect_timeout, ssl=ssl, **kwargs)
