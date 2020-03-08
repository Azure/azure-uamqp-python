#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import threading
import struct
import uuid
import logging
import time
from urllib.parse import urlparse
from enum import Enum

from ._transport import Transport, SSLTransport
from .session import Session
from .performatives import (
    HeaderFrame,
    OpenFrame,
    CloseFrame,
)
from .constants import (
    PORT, 
    SECURE_PORT,
    ConnectionState
)


_LOGGER = logging.getLogger(__name__)


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
        self.remote_idle_timeout_send_frame = None
        self.idle_timeout_empty_frame_send_ratio = kwargs.get('idle_timeout_empty_frame_send_ratio', 0.5)
        self.last_frame_received_time = None
        self.last_frame_sent_time = None

        self.outgoing_endpoints = {}
        self.incoming_endpoints = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
        self.listen()
        self._disconnect()

    def _set_state(self, new_state):
        # type: (ConnectionState) -> None
        """Update the connection state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        _LOGGER.info("Connection '%s' state changed: %r -> %r", self.container_id, previous_state, new_state)
        for session in self.outgoing_endpoints.values():
            session._on_connection_state_change()

    def _connect(self):
        if not self.state:
            self.transport.connect()
            self._set_state(ConnectionState.START)
        self.transport.negotiate()
        self._outgoing_HEADER()
        self._set_state(ConnectionState.HDR_SENT)
        if not self.allow_pipelined_open:
            self._process_incoming_frame(*self._read_frame())
            if self.state != ConnectionState.HDR_EXCH:
                self._disconnect()
                raise ValueError("Did not receive reciprocal protocol header. Disconnecting.")
        else:
            self._set_state(ConnectionState.HDR_SENT)

    def _disconnect(self, *args):
        if self.state == ConnectionState.END:
            return
        self._set_state(ConnectionState.END)
        self.transport.close()

    def _can_read(self):
        # type: () -> bool
        """Whether the connection is in a state where it is legal to read for incoming frames."""
        return self.state not in (ConnectionState.CLOSE_RCVD, ConnectionState.END)

    def _read_frame(self, wait=True, **kwargs):
        if self._can_read():
            if wait == False:
                with self.transport.non_blocking():
                    received = self.transport.receive_frame(**kwargs)
            elif wait == True:
                received = self.transport.receive_frame(**kwargs)
            else:
                with self.transport.having_timeout(timeout=wait):
                    received = self.transport.receive_frame(**kwargs)
     
            if received[1]:
                self.last_frame_received_time = time.time()
            return received
        _LOGGER.warning("Cannot read frame in current state: %r", self.state)

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

    def _send_frame(self, channel, frame, timeout=None, **kwargs):
        if self._can_write():
            self.last_frame_sent_time = time.time()
            if timeout:
                with self.transport.having_timeout(timeout):
                    self.transport.send_frame(channel, frame, **kwargs)
            self.transport.send_frame(channel, frame, **kwargs)
        else:
            _LOGGER.warning("Cannot write frame in current state: %r", self.state)

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
    
    def _outgoing_EMPTY(self):
        self._send_frame(0, None)

    def _outgoing_HEADER(self):
        header_frame = HeaderFrame()
        self.last_frame_sent_time = time.time()
        self._send_frame(0, header_frame)

    def _incoming_HEADER(self, channel, frame):
        if self.state == ConnectionState.START:
            self._set_state(ConnectionState.HDR_RCVD)
        elif self.state == ConnectionState.HDR_SENT:
            self._set_state(ConnectionState.HDR_EXCH)
        elif self.state == ConnectionState.OPEN_PIPE:
            self._set_state(ConnectionState.OPEN_SENT)

    def _outgoing_OPEN(self):
        open_frame = OpenFrame(
            container_id=self.container_id,
            hostname=self.hostname,
            max_frame_size=self.max_frame_size,
            channel_max=self.channel_max,
            idle_timeout=None,#self.idle_timeout * 1000 if self.idle_timeout else None,  # Convert to milliseconds
            outgoing_locales=self.outgoing_locales,
            incoming_locales=self.incoming_locales,
            offered_capabilities=self.offered_capabilities if self.state == ConnectionState.OPEN_RCVD else None,
            desired_capabilities=self.desired_capabilities if self.state == ConnectionState.HDR_EXCH else None,
            properties=self.properties,
        )
        self._send_frame(0, open_frame)

    def _incoming_OPEN(self, channel, frame):
        if channel != 0:
            _LOGGER.error("OPEN frame received on a channel that is not 0.")
            self.close(error=None)  # TODO: not allowed
            self._set_state(ConnectionState.END)
        if self.state == ConnectionState.OPENED:
            _LOGGER.error("OPEN frame received in the OPENED state.")
            self.close()
        if frame.idle_timeout:
            self.remote_idle_timeout = frame.idle_timeout/1000  # Convert to seconds
            self.remote_idle_timeout_send_frame = self.idle_timeout_empty_frame_send_ratio * self.remote_idle_timeout

        if frame.max_frame_size < 512:
            pass  # TODO: error
        self.remote_max_frame_size = frame.max_frame_size
        if self.state == ConnectionState.OPEN_SENT:
            self._set_state(ConnectionState.OPENED)
        elif self.state == ConnectionState.HDR_EXCH:
            self._set_state(ConnectionState.OPEN_RCVD)
            self._outgoing_OPEN()
            self._set_state(ConnectionState.OPENED)
        else:
            pass # TODO what now...?

    def _outgoing_CLOSE(self, error=None):
        close_frame = CloseFrame(error=error)
        self._send_frame(0, close_frame)

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
            self._set_state(ConnectionState.END)
            return
        if channel > self.channel_max:
            _LOGGER.error("Invalid channel")
        if frame.error:
            _LOGGER.error("Connection error: {}".format(frame.error))
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
        #self.incoming_endpoints.pop(channel)  # TODO
        #self.outgoing_endpoints.pop(channel)  # TODO

    def _process_incoming_frame(self, channel, frame):
        try:
            process = '_incoming_' + frame.NAME
            getattr(self, process)(channel, frame)
            return
        except AttributeError:
            pass
        try:
            getattr(self.incoming_endpoints[channel], process)(frame)
            return
        except NameError:
            time.sleep(0.1)  # Empty Frame or socket timeout
        except KeyError:
            pass  #TODO: channel error
        except AttributeError:
            _LOGGER.error("Unrecognized incoming frame: {}".format(frame))

    def _process_outgoing_frame(self, channel, frame):
        if not self.allow_pipelined_open and self.state in [ConnectionState.OPEN_PIPE, ConnectionState.OPEN_SENT]:
            raise ValueError("Connection not configured to allow pipeline send.")
        if self.state not in [ConnectionState.OPENED]:
            raise ValueError("Connection not open.")
        self._send_frame(channel, frame)
    
    def _get_local_timeout(self, now):
        if self.idle_timeout:
            time_since_last_received = now - self.last_frame_received_time
            return time_since_last_received > self.idle_timeout
        return False
    
    def _get_remote_timeout(self, now):
        if self.remote_idle_timeout:
            time_since_last_sent = now - self.last_frame_sent_time
            if time_since_last_sent > self.remote_idle_timeout_send_frame:
                self._outgoing_EMPTY()
        return False

    def listen(self, wait=False, **kwargs):
        if self.state == ConnectionState.END:
            raise ValueError("Connection closed.")
        new_frame = self._read_frame(wait=wait)
        if not new_frame:
            raise ValueError("Connection closed.")
        self._process_incoming_frame(*new_frame)
        if self.state not in [ConnectionState.OC_PIPE, ConnectionState.CLOSE_PIPE, ConnectionState.DISCARDING, ConnectionState.CLOSE_SENT]:
            now = time.time()
            for session in self.outgoing_endpoints.values():
                session._evaluate_timeout()
            if self._get_local_timeout(now) or self._get_remote_timeout(now):
                self.close(error=None, wait=wait)  # timeout

    def begin_session(self, session=None, block=True, **kwargs):
        assigned_channel = self._get_next_outgoing_channel()
        session = Session(self, assigned_channel, **kwargs)
        self.outgoing_endpoints[assigned_channel] = session
        if block and not self.allow_pipelined_open:  # TODO timeout
            session.begin()
        else:
            session.begin(block=False)
        return session

    def end_session(self, session, wait=True, **kwargs):
        if self.state in [ConnectionState.END, ConnectionState.CLOSE_SENT]:
            return
        try:
            if wait and not self.allow_pipelined_open:
                self.outgoing_endpoints[session.channel].end()
            else:
                self.outgoing_endpoints[session.channel].end(block=False)
        except KeyError:
            raise ValueError("No running session that matches input value.")

    def open(self, wait=True):
        self._connect()
        self._outgoing_OPEN()
        if self.state == ConnectionState.HDR_EXCH:
            self._set_state(ConnectionState.OPEN_SENT)
        elif self.state == ConnectionState.HDR_SENT:
            self._set_state(ConnectionState.OPEN_PIPE)
        if wait and not self.allow_pipelined_open:  # TODO: timeout
            while self.state != ConnectionState.OPENED:
                self.listen()

    def close(self, error=None, wait=True):
        if self.state in [ConnectionState.END, ConnectionState.CLOSE_SENT]:
            return
        self._outgoing_CLOSE(error=error)
        if self.state == ConnectionState.OPEN_PIPE:
            self._set_state(ConnectionState.OC_PIPE)
        elif self.state == ConnectionState.OPEN_SENT:
            self._set_state(ConnectionState.CLOSE_PIPE)
        elif error:
            self._set_state(ConnectionState.DISCARDING)
        else:
            self._set_state(ConnectionState.CLOSE_SENT)
        if wait:  # TODO: block for a timeout
            while self.state != ConnectionState.END:
                self.listen()
