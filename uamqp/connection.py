#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import threading
import queue
import struct
import uuid
from enum import Enum

from ._transport import SSLTransport
from .performatives import (
    HeaderFrame,
    OpenFrame,
    CloseFrame,
    _decode_frame,
    _encode_frame,
)

DEFAULT_LINK_CREDIT = 1000


def _unpack_frame_header(data):
    if len(data) != 8:
        raise ValueError("Invalid frame header")
    if data[0:4] == b'AMQP':  # AMQP header negotiation
        size = None
    else:
        size = struct.unpack('>I', data[0:4])[0]

    offset = struct.unpack('>B', data[4:5])[0]
    frame_type = struct.unpack('>B', data[5:6])[0]
    channel = struct.unpack('>H', data[6:])[0]
    return (size, offset, frame_type, channel)


class ConnectionState(Enum):
    #: In this state a Connection exists, but nothing has been sent or received. This is the state an
    #: implementation would be in immediately after performing a socket connect or socket accept.
    START = 0
    #: In this state the Connection header has been received from our peer, but we have not yet sent anything.
    HDR_RCVD = 1
    #: In this state the Connection header has been sent to our peer, but we have not yet received anything.
    HDR_SENT = 2
    #: In this state we have sent and received the Connection header, but we have not yet sent or
    #: received an open frame.
    HDR_EXCH = 3
    #: In this state we have sent both the Connection header and the open frame, but
    #: we have not yet received anything.
    OPEN_PIPE = 4
    #: In this state we have sent the Connection header, the open frame, any pipelined Connection traffic,
    #: and the close frame, but we have not yet received anything.
    OC_PIPE = 5
    #: In this state we have sent and received the Connection header, and received an open frame from
    #: our peer, but have not yet sent an open frame.
    OPEN_RCVD = 6
    #: In this state we have sent and received the Connection header, and sent an open frame to our peer,
    #: but have not yet received an open frame.
    OPEN_SENT = 7
    #: In this state we have send and received the Connection header, sent an open frame, any pipelined
    #: Connection traffic, and the close frame, but we have not yet received an open frame.
    CLOSE_PIPE = 8
    #: In this state the Connection header and the open frame have both been sent and received.
    OPENED = 9
    #: In this state we have received a close frame indicating that our partner has initiated a close.
    #: This means we will never have to read anything more from this Connection, however we can
    #: continue to write frames onto the Connection. If desired, an implementation could do a TCP half-close
    #: at this point to shutdown the read side of the Connection.
    CLOSE_RCVD = 10
    #: In this state we have sent a close frame to our partner. It is illegal to write anything more onto
    #: the Connection, however there may still be incoming frames. If desired, an implementation could do
    #: a TCP half-close at this point to shutdown the write side of the Connection.
    CLOSE_SENT = 11
    #: The DISCARDING state is a variant of the CLOSE_SENT state where the close is triggered by an error.
    #: In this case any incoming frames on the connection MUST be silently discarded until the peer's close
    #: frame is received.
    DISCARDING = 12
    #: In this state it is illegal for either endpoint to write anything more onto the Connection. The
    #: Connection may be safely closed and discarded.
    END = 13


class Connection(object):
    """
    :param str container_id: The ID of the source container.
    :param str hostname: The name of the target host.
    :param int max_frame_size: Proposed maximum frame size in bytes.
    :param int channel_max: The maximum channel number that may be used on the Connection.
    :param timedelta idle_timeout: Idle time-out in milliseconds.
    :param list(str) outgoing_locales: Locales available for outgoing text.
    :param list(str) incoming_locales: Desired locales for incoming text in decreasing level of preference.
    :param list(str) offered_capabilities: The extension capabilities the sender supports.
    :param list(str) desired_capabilities: The extension capabilities the sender may use if the receiver supports
    :param dict properties: Connection properties.
    """

    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self.state = None

        self.transport = kwargs.pop('transport', None) or SSLTransport(
            self.hostname,
            connect_timeout=kwargs.pop('connect_timeout', None),
            ssl=kwargs.pop('ssl', None),
            read_timeout=kwargs.pop('read_timeout', None),
            socket_settings=kwargs.pop('socket_settings', None),
            write_timeout=kwargs.pop('write_timeout', None)
        )
        self.container_id = kwargs.pop('container_id', None) or str(uuid.uuid4())
        self.max_frame_size = kwargs.pop('max_frame_size', None)
        self.channel_max = kwargs.pop('channel_max', None)
        self.idle_timeout = kwargs.pop('idle_timeout', None)
        self.outgoing_locales = kwargs.pop('outgoing_locales', [])
        self.incoming_locales = kwargs.pop('incoming_locales', [])
        self.offered_capabilities = kwargs.pop('offered_capabilities', [])
        self.desired_capabilities = kwargs.pop('desired_capabilities', [])

        self.allow_pipelined_open = kwargs.pop('allow_pipelined_open', False)
        self.remote_idle_timeout = None
        self.remote_idle_timeout_send_frame = None
        self.idle_timeout_empty_frame_send_ratio = None
        self.last_frame_received_time = None
        self.last_frame_sent_time = None

        self.sessions = {}
        self.endpoints = [
            {'OUTGOING': 0, 'INCOMING': 1}
        ]

        self._outgoing_frames = queue.Queue(maxsize=DEFAULT_LINK_CREDIT)
        self._incoming_frames = queue.Queue(maxsize=DEFAULT_LINK_CREDIT)
        self._thread_pool = kwargs.pop('executor', None)
        self._thread_lock = threading.Lock if self._thread_pool else None
        self._on_open_frame = kwargs.get('open_frame_hook')
        self._on_close_frame = kwargs.get('close_frame_hook')
        self._is_underlying_io_open = False
        self._idle_timeout_specified = False
        self._is_remote_frame_received = False

        self.properties = kwargs.pop('properties', None) or kwargs

    def __enter__(self):
        self.connect()
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
        self.disconnect()

    def _set_state(self, new_state):
        # type: (ConnectionState) -> None
        """Update the connection state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        print("Connection state changed: {} -> {}".format(previous_state, new_state))

    def _can_read(self):
        # type: () -> bool
        """Whether the connection is in a state where it is legal to read for incoming frames."""
        return self.state not in (ConnectionState.CLOSE_RCVD, ConnectionState.END)

    def _can_write(self):
        # type: () -> bool
        """Whether the connection is in a state where it is legal to write outgoing frames."""
        return self.state not in (
            ConnectionState.CLOSE_PIPE,
            ConnectionState.OC_PIPE,
            ConnectionState.CLOSE_SENT,
            ConnectionState.DISCARDING,
            ConnectionState.END
        )

    def _is_outgoing_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a frame can legally be sent, and if so, whether
        the successful sending of that frame will result in a change of state.
        """
        if self.state == ConnectionState.START:
            return isinstance(frame, HeaderFrame), ConnectionState.HDR_SENT
        if self.state == ConnectionState.HDR_RCVD:
            return isinstance(frame, HeaderFrame), ConnectionState.HDR_EXCH
        if self.state == ConnectionState.HDR_SENT:
            return isinstance(frame, OpenFrame), ConnectionState.OPEN_PIPE
        if self.state == ConnectionState.HDR_EXCH:
            return isinstance(frame, OpenFrame), ConnectionState.OPEN_SENT
        if self.state == ConnectionState.OPEN_RCVD:
            return isinstance(frame, OpenFrame), ConnectionState.OPENED
        if self.state == ConnectionState.OPEN_PIPE:
            return self.allow_pipelined_open, ConnectionState.OC_PIPE if isinstance(frame, CloseFrame) else None
        if self.state == ConnectionState.OPEN_SENT:
            return self.allow_pipelined_open, ConnectionState.CLOSE_PIPE if isinstance(frame, CloseFrame) else None
        if self.state == ConnectionState.OPENED:
            if isinstance(frame, CloseFrame):
                return True, ConnectionState.DISCARDING if frame.error else ConnectionState.CLOSE_SENT
            return True, None
        if self.state == ConnectionState.CLOSE_RCVD:
            return True, ConnectionState.END if isinstance(frame, CloseFrame) else None
        return False, None

    def _is_incoming_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a received frame is legal, and if so, whether
        it results in a change of connection state.
        """
        if self.state == ConnectionState.START:
            return isinstance(frame, HeaderFrame), ConnectionState.HDR_RCVD
        if self.state == ConnectionState.HDR_SENT:
            return isinstance(frame, HeaderFrame), ConnectionState.HDR_EXCH
        if self.state == ConnectionState.HDR_RCVD:
            return isinstance(frame, OpenFrame), None  # TODO: Should this be a state change?
        if self.state == ConnectionState.HDR_EXCH:
            return isinstance(frame, OpenFrame), ConnectionState.OPEN_RCVD
        if self.state == ConnectionState.OPEN_PIPE:
            return isinstance(frame, HeaderFrame), ConnectionState.OPEN_SENT
        if self.state == ConnectionState.OPEN_RCVD:
            return True, None  # TODO: Should there be a state change if a Close frame is received?
        if self.state == ConnectionState.OPEN_SENT:
            return isinstance(frame, OpenFrame), ConnectionState.OPENED
        if self.state == ConnectionState.OC_PIPE:
            return isinstance(frame, HeaderFrame), ConnectionState.CLOSE_PIPE
        if self.state == ConnectionState.CLOSE_PIPE:
            return isinstance(frame, OpenFrame), ConnectionState.CLOSE_SENT
        if self.state == ConnectionState.OPENED:
            return True, ConnectionState.CLOSE_RCVD if isinstance(frame, CloseFrame) else None
        if self.state in (ConnectionState.CLOSE_SENT, ConnectionState.DISCARDING):
            return True, ConnectionState.END if isinstance(frame, CloseFrame) else None
        return False, None

    def _run(self):
        if self._can_write():
            try:
                channel, outgoing_frame = self._outgoing_frames.get_nowait()
            except queue.Empty:
                pass
            else:
                can_send, next_state = self._is_outgoing_frame_legal(outgoing_frame)
                if can_send:
                    header, performative = _encode_frame(outgoing_frame)
                    if performative is None:
                        performative = header
                    else:
                        channel = struct.pack('>H', channel)
                        performative = header + channel + performative
                    self.transport.write(performative)
                    print("-> {}".format(outgoing_frame))
                    self._set_state(next_state)
                else:
                    raise TypeError("Attempt to send frame {} in illegal state {}".format(performative, self.state))
        if self._can_read():
            incoming_frame = self.blocking_read(unpack=_unpack_frame_header)
            performative = _decode_frame(incoming_frame[0], incoming_frame[3], incoming_frame[4] - 2)
            legal, new_state = self._is_incoming_frame_legal(performative)
            if legal:
                print("<- {}".format(performative))
                self._set_state(new_state)
                self._incoming_frames.put((incoming_frame[2], performative))
            else:
                raise TypeError("Received illegal frame {} in current state {}".format(performative, self.state))

    def begin_session(self, session, **kwargs):
        pass

    def end_session(self, session, **kwargs):
        pass

    def connect(self):
        try:
            if not self._is_underlying_io_open:
                self.transport.connect()
                self._is_underlying_io_open = True
                self._set_state(ConnectionState.START)
                if self._thread_pool:
                    self._thread_pool.__enter__()
            self._outgoing_frames.put((self.endpoints[0]['OUTGOING'], HeaderFrame()))
        except Exception:  # pylint: disable=broad-except
            self.disconnect()

    def blocking_read(self, timeout=None, **kwargs):
        with self.transport.having_timeout(timeout):
            return self.transport.read_frame(**kwargs)

    def disconnect(self, *args):
        self._set_state(ConnectionState.END)
        self.transport.close()
        self._thread_pool.__exit__(*args)

    def open(self, **kwargs):
        open_frame = kwargs.get('open_frame') or OpenFrame(
            container_id=self.container_id,
            hostname=self.hostname,
            max_frame_size=self.max_frame_size,
            channel_max=self.channel_max,
            idle_timeout=self.idle_timeout,
            outgoing_locales=self.outgoing_locales,
            incoming_locales=self.incoming_locales,
            offered_capabilities=self.offered_capabilities,
            desired_capabilities=self.desired_capabilities,
            properties=self.properties,
        )
        self._outgoing_frames.put((self.endpoints[0]['OUTGOING'], open_frame))

    def close(self, error=None):
        close_frame = CloseFrame(error=error)
        self._outgoing_frames.put((self.endpoints[0]['OUTGOING'], close_frame))

    def send_frame(self, frame, blocking=True):
        self._outgoing_frames.put((self.endpoints[0]['OUTGOING'], frame))
        if blocking:
            self._run()

    def receive_frame(self):
        self._run()
        _, frame = self._incoming_frames.get()
        return frame

    def do_work(self):
        self._run()
