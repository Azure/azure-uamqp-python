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
from .sasl import SASLTransport
from .session import Session
from .performatives import (
    OpenFrame,
    CloseFrame,
    BeginFrame,
    EndFrame,
)
from .constants import (
    PORT, 
    SECURE_PORT,
    MAX_CHANNELS,
    MAX_FRAME_SIZE_BYTES,
    HEADER_FRAME,
    ConnectionState
)


_LOGGER = logging.getLogger(__name__)
_CLOSING_STATES = (
    ConnectionState.OC_PIPE,
    ConnectionState.CLOSE_PIPE,
    ConnectionState.DISCARDING,
    ConnectionState.CLOSE_SENT,
    ConnectionState.END
)


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

        transport = kwargs.get('transport')
        if transport:
            self.transport = transport
        elif 'sasl_credential' in kwargs:
            self.transport = SASLTransport(
                host=parsed_url.netloc,
                credential=kwargs['sasl_credential'],
                **kwargs
            )
        else:
            self.transport = Transport(parsed_url.netloc, **kwargs)

        self.container_id = kwargs.pop('container_id', None) or str(uuid.uuid4())
        self.max_frame_size = kwargs.pop('max_frame_size', MAX_FRAME_SIZE_BYTES)
        self.remote_max_frame_size = None
        self.channel_max = kwargs.pop('channel_max', MAX_CHANNELS)
        self.idle_timeout = kwargs.pop('idle_timeout', None)
        self.outgoing_locales = kwargs.pop('outgoing_locales', None)
        self.incoming_locales = kwargs.pop('incoming_locales', None)
        self.offered_capabilities = None
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)
        self.properties = kwargs.pop('properties', None)

        self.allow_pipelined_open = kwargs.pop('allow_pipelined_open', True)
        self.remote_idle_timeout = None
        self.remote_idle_timeout_send_frame = None
        self.idle_timeout_empty_frame_send_ratio = kwargs.get('idle_timeout_empty_frame_send_ratio', 0.5)
        self.last_frame_received_time = None
        self.last_frame_sent_time = None
        self.idle_wait_time = kwargs.get('idle_wait_time', 0.1)
        self.network_trace = kwargs.get('network_trace', False)

        self.outgoing_endpoints = {}
        self.incoming_endpoints = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

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
        self._outgoing_header()
        self._set_state(ConnectionState.HDR_SENT)
        if not self.allow_pipelined_open:
            self._process_incoming_frame(*self._read_frame(wait=True))
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
                return self.transport.receive_frame(**kwargs)
            elif wait == True:
                with self.transport.block():
                    return self.transport.receive_frame(**kwargs)
            else:
                with self.transport.block_with_timeout(timeout=wait):
                    return self.transport.receive_frame(**kwargs)
        _LOGGER.warning("Cannot read frame in current state: %r", self.state)

    def _can_write(self):
        # type: () -> bool
        """Whether the connection is in a state where it is legal to write outgoing frames."""
        return self.state not in _CLOSING_STATES

    def _send_frame(self, channel, frame, timeout=None, **kwargs):
        if self._can_write():
            self.last_frame_sent_time = time.time()
            if timeout:
                with self.transport.block_with_timeout(timeout):
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
    
    def _outgoing_empty(self):
        self._send_frame(0, None)

    def _outgoing_header(self):
        self.last_frame_sent_time = time.time()
        self.transport.write(HEADER_FRAME)

    def _incoming_header(self, channel, frame):
        if self.network_trace:
                _LOGGER.info("<- Connection[%s] header(%r)", self.container_id, frame)
        if self.state == ConnectionState.START:
            self._set_state(ConnectionState.HDR_RCVD)
        elif self.state == ConnectionState.HDR_SENT:
            self._set_state(ConnectionState.HDR_EXCH)
        elif self.state == ConnectionState.OPEN_PIPE:
            self._set_state(ConnectionState.OPEN_SENT)

    def _outgoing_open(self):
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

    def _incoming_open(self, channel, frame):
        if channel != 0:
            _LOGGER.error("OPEN frame received on a channel that is not 0.")
            self.close(error=None)  # TODO: not allowed
            self._set_state(ConnectionState.END)
        if self.state == ConnectionState.OPENED:
            _LOGGER.error("OPEN frame received in the OPENED state.")
            self.close()
        if frame[4]:  # idle_timeout
            self.remote_idle_timeout = frame[4]/1000  # Convert to seconds
            self.remote_idle_timeout_send_frame = self.idle_timeout_empty_frame_send_ratio * self.remote_idle_timeout

        if frame[2] < 512:  # max_frame_size
            pass  # TODO: error
        self.remote_max_frame_size = frame[2]
        if self.state == ConnectionState.OPEN_SENT:
            self._set_state(ConnectionState.OPENED)
        elif self.state == ConnectionState.HDR_EXCH:
            self._set_state(ConnectionState.OPEN_RCVD)
            self._outgoing_open()
            self._set_state(ConnectionState.OPENED)
        else:
            pass # TODO what now...?

    def _outgoing_close(self, error=None):
        close_frame = CloseFrame(error=error)
        self._send_frame(0, close_frame)

    def _incoming_close(self, channel, frame):
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
        if frame[0]:  # error
            _LOGGER.error("Connection error: {}".format(frame[0]))
        self._set_state(ConnectionState.CLOSE_RCVD)
        self._outgoing_close()
        self._disconnect()
        self._set_state(ConnectionState.END)

    def _incoming_begin(self, channel, frame):
        try:
            existing_session = self.outgoing_endpoints[frame[0]]  # remote_channel
            self.incoming_endpoints[channel] = existing_session
            self.incoming_endpoints[channel]._incoming_begin(frame)
        except KeyError:
            new_session = Session.from_incoming_frame(self, channel, frame)
            self.incoming_endpoints[channel] = new_session
            new_session._incoming_begin(frame)

    def _incoming_end(self, channel, frame):
        try:
            self.incoming_endpoints[channel]._incoming_end(frame)
        except KeyError:
            pass  # TODO: channel error
        #self.incoming_endpoints.pop(channel)  # TODO
        #self.outgoing_endpoints.pop(channel)  # TODO

    def _process_incoming_frame(self, channel, frame):
        try:
            performative, fields = frame
        except TypeError:
            return True  # Empty Frame or socket timeout
        try:
            self.last_frame_received_time = time.time()
            if performative == 20:
                self.incoming_endpoints[channel]._incoming_transfer(fields)
                return False
            if performative == 21:
                self.incoming_endpoints[channel]._incoming_disposition(fields)
                return False
            if performative == 19:
                self.incoming_endpoints[channel]._incoming_flow(fields)
                return False
            if performative == 18:
                self.incoming_endpoints[channel]._incoming_attach(fields)
                return False
            if performative == 22:
                self.incoming_endpoints[channel]._incoming_detach(fields)
                return True
            if performative == 17:
                if self.network_trace:
                    _LOGGER.info("<- Connection[%s] %r", self.container_id, BeginFrame(*fields))
                self._incoming_begin(channel, fields)
                return True
            if performative == 23:
                if self.network_trace:
                    _LOGGER.info("<- Connection[%s] %r", self.container_id, EndFrame(*fields))
                self._incoming_end(channel, fields)
                return True
            if performative == 16:
                if self.network_trace:
                    _LOGGER.info("<- Connection[%s] %r", self.container_id, OpenFrame(*fields))
                self._incoming_open(channel, fields)
                return True
            if performative == 24:
                if self.network_trace:
                    _LOGGER.info("<- Connection[%s] %r", self.container_id, CloseFrame(*fields))
                self._incoming_close(channel, fields)
                return True
            if performative == 0:
                if self.network_trace:
                    _LOGGER.info("<- Connection[%s] header(%r)", self.container_id, fields)
                self._incoming_header(channel, fields)
                return True
            if performative == 1:
                return False  # TODO: incoming EMPTY
            else:
                _LOGGER.error("Unrecognized incoming frame: {}".format(frame))
                return True
        except KeyError:
            return True  #TODO: channel error

    def _process_outgoing_frame(self, channel, frame):
        if not self.allow_pipelined_open and self.state in [ConnectionState.OPEN_PIPE, ConnectionState.OPEN_SENT]:
            raise ValueError("Connection not configured to allow pipeline send.")
        if self.state not in [ConnectionState.OPEN_PIPE, ConnectionState.OPEN_SENT, ConnectionState.OPENED]:
            raise ValueError("Connection not open.")
        if self.network_trace:
            _LOGGER.info("-> Connection[%s] %r", self.container_id, frame)
        self._send_frame(channel, frame)

    def _get_local_timeout(self, now):
        if self.idle_timeout and self.last_frame_received_time:
            time_since_last_received = now - self.last_frame_received_time
            return time_since_last_received > self.idle_timeout
        return False

    def _get_remote_timeout(self, now):
        if self.remote_idle_timeout and self.last_frame_sent_time:
            time_since_last_sent = now - self.last_frame_sent_time
            if time_since_last_sent > self.remote_idle_timeout_send_frame:
                self._outgoing_empty()
        return False
    
    def _wait_for_response(self, wait, end_state):
        # type: (Union[bool, float], ConnectionState) -> None
        if wait == True:
            self.listen(wait=False)
            while self.state != end_state:
                time.sleep(self.idle_wait_time)
                self.listen(wait=False)
        elif wait:
            self.listen(wait=False)
            timeout = time.time() + wait
            while self.state != end_state:
                if time.time() >= timeout:
                    break
                time.sleep(self.idle_wait_time)
                self.listen(wait=False)

    def listen(self, wait=False, batch=1, **kwargs):
        if self.state == ConnectionState.END:
            raise ValueError("Connection closed.")
        for _ in range(batch):
            new_frame = self._read_frame(wait=wait, **kwargs)
            if not new_frame:
                raise ValueError("Connection closed.")
            if self._process_incoming_frame(*new_frame):
                break
        if self.state not in _CLOSING_STATES:
            now = time.time()
            if self._get_local_timeout(now) or self._get_remote_timeout(now):
                self.close(error=None, wait=False)

    def create_session(self, **kwargs):
        assigned_channel = self._get_next_outgoing_channel()
        kwargs['allow_pipelined_open'] = self.allow_pipelined_open
        kwargs['idle_wait_time'] = self.idle_wait_time
        session = Session(
            self,
            assigned_channel,
            network_trace=kwargs.pop('network_trace', self.network_trace),
            **kwargs)
        self.outgoing_endpoints[assigned_channel] = session
        return session

    def open(self, wait=False):
        self._connect()
        self._outgoing_open()
        if self.state == ConnectionState.HDR_EXCH:
            self._set_state(ConnectionState.OPEN_SENT)
        elif self.state == ConnectionState.HDR_SENT:
            self._set_state(ConnectionState.OPEN_PIPE)
        if wait:
            self._wait_for_response(wait, ConnectionState.OPENED)
        elif not self.allow_pipelined_open:
            raise ValueError("Connection has been configured to not allow piplined-open. Please set 'wait' parameter.")

    def close(self, error=None, wait=False):
        if self.state in [ConnectionState.END, ConnectionState.CLOSE_SENT]:
            return
        self._outgoing_close(error=error)
        if self.state == ConnectionState.OPEN_PIPE:
            self._set_state(ConnectionState.OC_PIPE)
        elif self.state == ConnectionState.OPEN_SENT:
            self._set_state(ConnectionState.CLOSE_PIPE)
        elif error:
            self._set_state(ConnectionState.DISCARDING)
        else:
            self._set_state(ConnectionState.CLOSE_SENT)
        self._wait_for_response(wait, ConnectionState.END)
        self._disconnect()
