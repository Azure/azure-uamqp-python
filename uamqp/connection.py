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
import time
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
_LOGGER = logging.getLogger(__name__)


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
        self.remote_max_frame_size = None
        self.channel_max = kwargs.pop('channel_max', None)
        self.idle_timeout = kwargs.pop('idle_timeout', None)
        self.outgoing_locales = kwargs.pop('outgoing_locales', None)
        self.incoming_locales = kwargs.pop('incoming_locales', None)
        self.offered_capabilities = None
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)
        self.properties = kwargs.pop('properties', None)

        self.allow_pipelined_open = kwargs.pop('allow_pipelined_open', False)
        self.remote_idle_timeout = None
        self.remote_idle_timeout_send_frame_ms = None
        self.idle_timeout_empty_frame_send_ratio = None
        self.last_frame_received_time = None
        self.last_frame_sent_time = None

        self.outgoing_endpoints = {}
        self.incoming_endpoints = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
        self._disconnect()

    def _set_state(self, new_state):
        # type: (ConnectionState) -> None
        """Update the connection state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        _LOGGER.info("Connection '{}' state changed: {} -> {}".format(self.container_id, previous_state, new_state))
        for session in self.outgoing_endpoints.values():
            session._on_connection_state_change()

    def _connect(self):
        if not self.state:
            self.transport.connect()
            self._set_state(ConnectionState.START)

        self.transport.negotiate()
        self._outgoing_HEADER()
        if not self.allow_pipelined_open:
            self._run()
            if self.state not in (ConnectionState.HDR_EXCH,):
                LOGGER.warning("Did not receive reciprocal protocol header. Disconnecting.")
                self._disconnect()

    def _read_frame(self, timeout=None, **kwargs):
        if timeout:
            with self.transport.having_timeout(timeout):
                return self.transport.receive_frame(**kwargs)
        return self.transport.receive_frame(**kwargs)

    def _disconnect(self, *args):
        if self.state == ConnectionState.END:
            return
        self._set_state(ConnectionState.END)
        self.transport.close()

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
        next_channel = next(i for i in range(1, self.channel_max) if i not in self.outgoing_endpoints)
        return next_channel

    def _outgoing_HEADER(self):
        header_frame = HeaderFrame()
        self.last_frame_sent_time = time.time()
        self.transport.send_frame(0, header_frame)

    def _incoming_HEADER(self):
        if self.state == ConnectionState.START:
            self._set_state(ConnectionState.HDR_RCVD)
        if self.state == ConnectionState.HDR_SENT:
            self._set_state(ConnectionState.HDR_EXCH)

    def _outgoing_OPEN(self):
        open_frame = OpenFrame(
            container_id=self.container_id,
            hostname=self.hostname,
            max_frame_size=self.max_frame_size,
            channel_max=self.channel_max,
            idle_timeout=self.idle_timeout,
            outgoing_locales=self.outgoing_locales,
            incoming_locales=self.incoming_locales,
            offered_capabilities=self.offered_capabilities if self.state == ConnectionState.OPEN_RCVD else None,
            desired_capabilities=self.desired_capabilities if self.state == ConnectionState.HDR_EXCH else None,
            properties=self.properties,
        )
        self.last_frame_sent_time = time.time()
        self.transport.send_frame(0, open_frame)

    def _incoming_OPEN(self, channel, frame):
        if channel != 0:
            _LOGGER.error("OPEN frame received on a channel that is not 0.")
            self.close(error=None)  # TODO: not allowed
            self._set_state(ConnectionState.END)
        if self.state == ConnectionState.OPENED:
            _LOGGER.error("OPEN frame received in the OPENED state.")
            self.close()
        self.remote_idle_timeout = frame.idle_timeout
        if frame.max_frame_size < 512:
            pass  # TODO: error
        self.remote_max_frame_size = frame.max_frame_size
        if self.state == ConnectionState.OPEN_SENT:
            self._set_state(ConnectionState.OPENED)
        elif self.state == ConnectionState.HDR_EXCH:
            self._set_state(ConnectionState.OPEN_RCVD)
            self._outgoing_OPEN()
        else:
            pass # TODO what now...?

    def _outgoing_CLOSE(self, error=None):
        close_frame = CloseFrame(error=error)
        self.last_frame_sent_time = time.time()
        self.transport.send_frame(0, close_frame)

    def _incoming_CLOSE(self, channel, frame):
        disconnect_states = [
            ConnectionState.HDR_RCVD,
            ConnectionState.HDR_EXCH,
            ConnectionState.OPEN_RCVD,
            ConnectionState.CLOSE_SENT,
            ConnectionState.DISCARDING
        ]
        if self.state in disconnect_states:
            self._disconnect()
            return
        if channel > self.channel_max:
            _LOGGER("Invalid channel")
        if frame.error:
            _LOGGER("Connection error: {}".format(frame.error))
        self._set_state(ConnectionState.CLOSE_RCVD)
        self._outgoing_CLOSE()
        self._disconnect()
        self._set_state(ConnectionState.END)

    def _incoming_BEGIN(self, channel, frame):
        try:
            existing_session = self.outgoing_endpoints[frame.remote_channel]
            self.incoming_endpoints[channel] = existing_session
            self.incoming_endpoints[channel]._incoming_BEGIN(frame)
        except KeyError:
            new_session = Session.from_incoming_frame(self, channel, frame)
            self.incoming_endpoints[channel] = new_session
            new_session._incoming_BEGIN(frame)

    def _incoming_END(self, channel, frame):
        try:
            self.incoming_endpoints[channel]._incoming_END(frame)
        except KeyError:
            pass  # TODO: channel error
        self.incoming_endpoints.pop(channel)
        self.outgoing_endpoints.pop(channel)

    def _process_incoming_frame(self, channel, frame):
        self.last_frame_received_time = time.time()
        process = '_incoming_' + frame.NAME
        try:
            getattr(self, process)(channel, frame)
            return
        except AttributeError:
            try:
                getattr(self.incoming_endpoints[channel], process)(frame)
                return
            except KeyError:
                pass  #TODO: channel error
            except AttributeError:
                _LOGGER.error("Unrecognized incoming frame: {}".format(e))
            except Exception as e:
                _LOGGER.error("Error processing incoming frame: {}".format(e))
        except Exception as e:
            _LOGGER.error("Error processing incoming frame: {}".format(e))

    def _process_outgoing_frame(self, channel, frame):
        if self.state != ConnectionState.OPENED:
            raise ValueError("Connection not open")
        self.last_frame_sent_time = time.time()
        self.transport.send_frame(channel, frame)

    def _run(self):
        if self._can_read():
            channel, incoming_frame = self._read_frame()
            legal, new_state = self._is_incoming_frame_legal(incoming_frame)
            if legal:
                self._set_state(new_state)
                self._process_incoming_frame(channel, incoming_frame)
            else:
                raise TypeError("Received illegal frame {} in current state {}".format(
                    type(incoming_frame), self.state))

    def begin_session(self, session=None, block=False, **kwargs):
        assigned_channel = self._get_next_outgoing_channel()
        session = session or Session(assigned_channel, **kwargs)
        self.outgoing_endpoints[assigned_channel] = session
        session.begin()
        if block:
            self.do_work()
        return session

    def end_session(self, session, block=False, **kwargs):
        try:
            self.outgoing_endpoints[session.channel].end()
            if block:
                self.do_work()
        except KeyError:
            raise ValueError("No running session that matches input value.")

    def open(self, **kwargs):
        self._connect()
        self._outgoing_OPEN()
        self._set_state(ConnectionState.OPEN_SENT)

    def close(self, error=None):
        self._outgoing_CLOSE(error=error)
        if error:
            self._set_state(ConnectionState.DISCARDING)
        else:
            self._set_state(ConnectionState.CLOSE_SENT)
