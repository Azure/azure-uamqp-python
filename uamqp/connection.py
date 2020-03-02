#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import threading
import queue
import struct
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse
from enum import Enum

from ._transport import Transport, SSLTransport
from .session import Session
from .performatives import (
    HeaderFrame,
    OpenFrame,
    CloseFrame,
)
from .constants import PORT, SECURE_PORT


DEFAULT_LINK_CREDIT = 1000
LOGGER = logging.getLogger(__name__)


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


class EmptyChannel(queue.Queue):

    def outgoing_frame(self):
        frame = self.get_nowait()
        self.task_done()
        return frame

    incoming_frame = queue.Queue.put

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

    def __init__(self, endpoint, **kwargs):
        parsed_url = urlparse(endpoint)
        self.hostname = parsed_url.hostname
        if parsed_url.port:
            self.port = parsed_url.port
        elif parsed_url.scheme == 'amqps':
            self.port = SECURE_PORT
        else:
            self.port = PORT
        self.state = None

        self.transport = kwargs.pop('transport', None) or Transport(
            parsed_url.netloc,
            connect_timeout=kwargs.pop('connect_timeout', None),
            ssl={'server_hostname': self.hostname},
            read_timeout=kwargs.pop('read_timeout', None),
            socket_settings=kwargs.pop('socket_settings', None),
            write_timeout=kwargs.pop('write_timeout', None)
        )
        self.container_id = kwargs.pop('container_id', None) or str(uuid.uuid4())
        self.max_frame_size = kwargs.pop('max_frame_size', None)
        self.channel_max = kwargs.pop('channel_max', None)
        self.idle_timeout = kwargs.pop('idle_timeout', None)
        self.outgoing_locales = kwargs.pop('outgoing_locales', None)
        self.incoming_locales = kwargs.pop('incoming_locales', None)
        self.offered_capabilities = kwargs.pop('offered_capabilities', None)
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)

        self.allow_pipelined_open = kwargs.pop('allow_pipelined_open', False)
        self.remote_idle_timeout = None
        self.remote_idle_timeout_send_frame = None
        self.idle_timeout_empty_frame_send_ratio = None
        self.last_frame_received_time = None
        self.last_frame_sent_time = None

        self.outgoing_endpoints = {
            0: EmptyChannel(maxsize=DEFAULT_LINK_CREDIT)  # Initial outgoing channel
        }
        self.incoming_endpoints = {
            0: EmptyChannel(maxsize=DEFAULT_LINK_CREDIT)  # Initial incoming channel
        }

        self._thread_pool = kwargs.pop('executor', None)
        self._thread_lock = threading.Lock if self._thread_pool else None
        self._on_receive_open_frame = kwargs.pop('open_frame_hook', None)
        self._on_receive_close_frame = kwargs.pop('close_frame_hook', None)
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

    def _get_next_outgoing_channel(self):
        # type: () -> int
        """Get the next available outgoing channel number within the max channel limit.

        :raises ValueError: If maximum channels has been reached.
        :returns: The next available outgoing channel number.
        :rtype: int
        """
        if (len(self.incoming_endpoints) + len(self.outgoing_endpoints)) >= self.channel_max:
            raise ValueError("Maximum number of channels ({}) has been reached.".format(self.channel_max))
        next_channel = next(i for i in range(1, self.channel_max) if i not in self.incoming_endpoints)
        return next_channel

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
            if isinstance(frame, CloseFrame):
                return True, ConnectionState.CLOSE_RCVD
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

    def _process_incoming_frame(self, channel, frame):
        if isinstance(frame, OpenFrame):
            self.max_frame_size = frame.max_frame_size
            self.channel_max = frame.channel_max
            self.remote_idle_timeout = frame.idle_timeout
        elif isinstance(frame, HeaderFrame):
            self.incoming_endpoints[channel].incoming_frame(frame)
        elif isinstance(frame, CloseFrame):
            return  # TODO: Process close receipt
        else:
            incoming_channel = 1
            if incoming_channel in self.incoming_endpoints:
                self.incoming_endpoints[incoming_channel].incoming_frame(frame)
            elif incoming_channel in self.outgoing_endpoints:
                self.incoming_endpoints[incoming_channel] = self.outgoing_endpoints[incoming_channel]
                self.incoming_endpoints[incoming_channel].incoming_frame(frame)
            else:
                raise ValueError("unknown channel", self.incoming_endpoints, self.outgoing_endpoints)

    def _run(self):
        for channel, endpoint in self.outgoing_endpoints.items():
            while self._can_write():
                try:
                    outgoing_frame = endpoint.outgoing_frame()
                    if outgoing_frame:
                        can_send, next_state = self._is_outgoing_frame_legal(outgoing_frame)
                        if can_send:
                            self.last_frame_sent_time = datetime.now()
                            self.transport.send_frame(channel, outgoing_frame)
                            self._set_state(next_state)
                        else:
                            raise TypeError("Attempt to send frame {} in illegal state {}".format(
                                type(outgoing_frame), self.state))
                    else:
                        break  # This Session cannot write. Skip.
                except queue.Empty:
                    break  # Move to next endpoint if this queue is empty
            else:
                break  # Stop looping all endpoints if connection can no longer write

        if self._can_read():
            channel, incoming_frame = self.transport.receive_frame()
            legal, new_state = self._is_incoming_frame_legal(incoming_frame)
            if legal:
                self._is_remote_frame_received = True
                self.last_frame_received_time = datetime.now()
                self._set_state(new_state)
                self._process_incoming_frame(channel, incoming_frame)
            else:
                raise TypeError("Received illegal frame {} in current state {}".format(
                    type(incoming_frame), self.state))

    def begin_session(self, session=None, **kwargs):
        assigned_channel = self._get_next_outgoing_channel()
        session = session or Session(assigned_channel, **kwargs)
        self.outgoing_endpoints[assigned_channel] = session
        session.begin()
        return session

    def end_session(self, session, **kwargs):
        try:
            self.outgoing_endpoints[session.channel].end()
        except KeyError:
            raise ValueError("No running session that matches input value.")

    def connect(self):
        if not self._is_underlying_io_open:
            self.transport.connect()
            self._is_underlying_io_open = True
            self._set_state(ConnectionState.START)
            if self._thread_pool:
                self._thread_pool.__enter__()

        self.transport.negotiate()
        self.outgoing_endpoints[0].put(HeaderFrame())
        if not self.allow_pipelined_open:
            self.do_work()
            try:
                incoming_header = self.incoming_endpoints[0].get_nowait()
                if not isinstance(incoming_header, HeaderFrame):
                    raise ValueError("Expected AMQP protocol header, received {}".format(incoming_header))
            except queue.Empty:
                if self.state not in (ConnectionState.HDR_EXCH):
                    LOGGER.warning("Did not receive reciprocal protocol header. Disconnecting.")
                    self.disconnect()

    def blocking_read(self, timeout=None, **kwargs):
        with self.transport.having_timeout(timeout):
            return self.transport.read_frame(**kwargs)

    def disconnect(self, *args):
        self._set_state(ConnectionState.END)
        self.transport.close()
        if self._thread_pool:
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
        self.outgoing_endpoints[0].put(open_frame)

    def close(self, error=None):
        close_frame = CloseFrame(error=error)
        self.outgoing_endpoints[0].put(close_frame)

    def do_work(self):
        self._run()
