#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import queue
import uuid
import logging
from enum import Enum

from .constants import INCOMING_WINDOW, OUTGOING_WIDNOW
from .endpoints import Source, Target
from .sender import SenderLink
from .receiver import ReceiverLink
from .performatives import (
    BeginFrame,
    EndFrame,
    FlowFrame,
    AttachFrame,
    DetachFrame,
    TransferFrame,
    DispositionFrame
)


DEFAULT_LINK_CREDIT = 1000
_LOGGER = logging.getLogger(__name__)


class SessionState(Enum):
    #: In the UNMAPPED state, the Session endpoint is not mapped to any incoming or outgoing channels on the
    #: Connection endpoint. In this state an endpoint cannot send or receive frames.
    UNMAPPED = 0
    #: In the BEGIN_SENT state, the Session endpoint is assigned an outgoing channel number, but there is no entry
    #: in the incoming channel map. In this state the endpoint may send frames but cannot receive them.
    BEGIN_SENT = 1
    #: In the BEGIN_RCVD state, the Session endpoint has an entry in the incoming channel map, but has not yet
    #: been assigned an outgoing channel number. The endpoint may receive frames, but cannot send them.
    BEGIN_RCVD = 2
    #: In the MAPPED state, the Session endpoint has both an outgoing channel number and an entry in the incoming
    #: channel map. The endpoint may both send and receive frames.
    MAPPED = 3
    #: In the END_SENT state, the Session endpoint has an entry in the incoming channel map, but is no longer
    #: assigned an outgoing channel number. The endpoint may receive frames, but cannot send them.
    END_SENT = 4
    #: In the END_RCVD state, the Session endpoint is assigned an outgoing channel number, but there is no entry in
    #: the incoming channel map. The endpoint may send frames, but cannot receive them.
    END_RCVD = 5
    #: The DISCARDING state is a variant of the END_SENT state where the end is triggered by an error. In this
    #: case any incoming frames on the session MUST be silently discarded until the peer’s end frame is received.
    DISCARDING = 6


class SessionTransferState(Enum):

    Okay = 0
    Error = 1
    Busy = 2


class Session(object):
    """
    :param int remote_channel: The remote channel for this Session.
    :param int next_outgoing_id: The transfer-id of the first transfer id the sender will send.
    :param int incoming_window: The initial incoming-window of the sender.
    :param int outgoing_window: The initial outgoing-window of the sender.
    :param int handle_max: The maximum handle value that may be used on the Session.
    :param list(str) offered_capabilities: The extension capabilities the sender supports.
    :param list(str) desired_capabilities: The extension capabilities the sender may use if the receiver supports
    :param dict properties: Session properties.
    """

    def __init__(self, connection, channel, **kwargs):
        self.name = kwargs.pop('name', None) or str(uuid.uuid4())
        self.state = SessionState.UNMAPPED
        self.handle_max = kwargs.get('handle_max', 4294967295)
        self.properties = kwargs.pop('properties', None)
        self.channel = channel
        self.remote_channel = None
        self.next_outgoing_id = kwargs.pop('next_outgoing_id', 0)
        self.next_incoming_id = None
        self.incoming_window = kwargs.pop('incoming_window', 1)
        self.outgoing_window = kwargs.pop('outgoing_window', 1)
        self.target_incoming_window = self.incoming_window
        self.remote_incoming_window = 0
        self.remote_outgoing_window = 0
        self.offered_capabilities = None
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)

        self.links = {}
        self._connection = connection
        self._output_handles = {}
        self._input_handles = {}
        self._outgoing_frames = queue.Queue()

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, *args):
        self.end()

    @classmethod
    def from_incoming_frame(cls, connection, channel, frame):
        # check session_create_from_endpoint in C lib
        new_session = cls(connection, channel)
        new_session._incoming_BEGIN(frame)
        return new_session

    def _set_state(self, new_state):
        # type: (SessionState) -> None
        """Update the session state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        _LOGGER.info("Session '{}' state changed: {} -> {}".format(self.name, previous_state, new_state))
        for link in self.links.values():
            link._on_session_state_change()

    def _on_connection_state_change(self):
        if self._connection.state == ConnectionState.CLOSE_RCVD or self._connection.state == ConnectionState.END:
            self._set_state(SessionState.DISCARDING)
        elif self._connection.state == ConnectionState.ERROR:
            self._set_state(SessionState.ERROR)

    def _get_next_output_handle(self):
        # type: () -> int
        """Get the next available outgoing handle number within the max handle limit.

        :raises ValueError: If maximum handle has been reached.
        :returns: The next available outgoing handle number.
        :rtype: int
        """
        if len(self._output_handles) >= self.handle_max:
            raise ValueError("Maximum number of handles ({}) has been reached.".format(self.handle_max))
        next_handle = next(i for i in range(1, self.handle_max) if i not in self._output_handles)
        return next_handle
    
    def _outgoing_BEGIN(self):
        begin_frame = BeginFrame(
            remote_channel=self.remote_channel if self.state == SessionState.BEGIN_RCVD else None,
            next_outgoing_id=self.next_outgoing_id,
            outgoing_window=self.outgoing_window,
            incoming_window=self.incoming_window,
            handle_max=self.handle_max,
            offered_capabilities=self.offered_capabilitiesis if self.state == SessionState.BEGIN_RCVD else None,
            desired_capabilities=self.desired_capabilities if self.state == SessionState.UNMAPPED else None,
            properties=self.properties,
        )
        self._connection._process_outgoing_frame(self.channel, begin_frame)

    def _incoming_BEGIN(self, frame):
        self.handle_max = frame.handle_max
        self.next_incoming_id = frame.next_outgoing_id
        self.remote_incoming_window = frame.incoming_window
        self.remote_outgoing_window = frame.outgoing_window
        if self.state == SessionState.BEGIN_SENT:
            self.remote_channel = frame.remote_channel
            self._set_state(SessionState.MAPPED)
        elif self.state == SessionState.UNMAPPED:
            self._set_state(SessionState.BEGIN_RCVD)
            self._outgoing_BEGIN()
            self._set_state(SessionState.MAPPED)

    def _outgoing_END(self, error=None):
        end_frame = EndFrame(error=error)
        self._connection._outgoing_END(self.channel, end_frame)

    def _incoming_END(self, frame):
        if self.state not in [SessionState.END_RCVD, SessionState.END_SENT, SessionState.DISCARDING]:
            self._set_state(SessionState.END_RCVD)
            # TODO: Clean up all links
            self._outgoing_END()
        self._set_state(SessionState.UNMAPPED)

    def _outgoing_ATTACH(self, frame):
        self._connection._process_outgoing_frame(self.channel, frame)

    def _incoming_ATTACH(self, frame):
        try:
            self._input_handles[frame.handle] = self.links[frame.name]
            self._input_handles[frame.handle]._incoming_ATTACH(frame)
        except KeyError:
            outgoing_handle = self._get_next_output_handle()  # TODO: catch max-handles error
            if frame.role == 'SENDER':
                new_link = ReceiverLink.from_incoming_frame(self, outgoing_handle, frame)
            else:
                new_link = SenderLink.from_incoming_frame(self, outgoing_handle, frame)
            new_link._incoming_ATTACH(frame)
            self.links[frame.name] = new_link
            self._output_handles[outgoing_handle] = new_link
            self._input_handles[frame.handle] = new_link
    
    def _outgoing_FLOW(self, frame=None):
        flow_frame = frame or FlowFrame()
        flow_frame.next_incoming_id = self.next_incoming_id,
        flow_frame.incoming_window = self.incoming_window,
        flow_frame.next_outgoing_id = self.next_outgoing_id,
        flow_frame.outgoing_window = self.outgoing_window,
        self._connection._process_outgoing_frame(self.channel, flow_frame)

    def _incoming_FLOW(self, frame):
        self.next_incoming_id = frame.next_outgoing_id
        remote_incoming_id = frame.next_incoming_id or self.next_outgoing_id  # TODO "initial-outgoing-id"
        self.remote_incoming_window = remote_incoming_id + frame.incoming_window - self.next_outgoing_id
        self.remote_outgoing_window = frame.outgoing_window
        if frame.handle:
            self._input_handles[frame.handle].incoming_frame(frame)
        while self.remote_incoming_window > 0:
            for link in self._output_handles.values():
                link._incoming_FLOW(frame)

    def _outgoing_TRANSFER(self, delivery):
        if self.state != SessionState.MAPPED:
            delivery.transfer_state = SessionTransferState.Error
        if self.remote_incoming_window <= 0:
            delivery.transfer_state = SessionTransferState.Busy
        else:
            delivery.frame.delivery_id = self.next_outgoing_id
            self._connection._process_outgoing_frame(self.channel, delivery.frame)
            self.next_outgoing_id += 1
            self.remote_incoming_window -= 1
            self.outgoing_window -= 1
            delivery.transfer_state = SessionTransferState.Okay
            # TODO validate max frame size and break into multipl deliveries

    def _incoming_TRANSFER(self, frame):
        self.next_incoming_id += 1
        self.remote_outgoing_window -= 1
        self.incoming_window -= 1
        try:
            self._input_handles[frame.handle]._incoming_TRANSFER(frame)
        except KeyError:
            pass  #TODO: "unattached handle"
        if self.incoming_window == 0:
            self.incoming_window = self.target_incoming_window
            self._outgoing_FLOW()

    def _outgoing_DISPOSITION(self, frame):
        self._connection._process_outgoing_frame(self.channel, frame)

    def _incoming_DISPOSITION(self, frame):
        for link in self._input_handles.values():
            link._incoming_DISPOSITION(frame)

    def _outgoing_DETACH(self, frame):
        self._connection._process_outgoing_frame(self.channel, frame)

    def _incoming_DETACH(self, frame):
        try:
            link = self._input_handles[frame.handle]
            link._incoming_DETACH(frame)
            if link._is_closed:
                del self.links[link.name]
                del self._input_handles[link.remote_handle]
                del self._output_handles[link.handle]
        except KeyError:
            pass  # TODO: close session with unattached-handle

    def begin(self):
        self._outgoing_BEGIN()
        self._set_state(SessionState.BEGIN_SENT)

    def end(self, error=None):
        # type: (Optional[AMQPError]) -> None
        if self.state not in [SessionState.UNMAPPED, SessionState.DISCARDING]:
            self._outgoing_END(error=error)
        # TODO: destroy all links
        if error:
            self._set_state(SessionState.DISCARDING)
        else:
            self._set_state(SessionState.END_SENT)

    def attach_receiver_link(self, **kwargs):
        assigned_handle = self._get_next_output_handle()
        link = ReceiverLink(handle=assigned_handle, **kwargs)
        self.links[link.name] = link
        self._output_handles[assigned_handle] = link
        link.attach()
        return link

    def attach_sender_link(self, **kwargs):
        assigned_handle = self._get_next_output_handle()
        link = SenderLink(handle=assigned_handle, **kwargs)
        self._output_handles[assigned_handle] = link
        self.links[link.name] = link
        link.attach()
        return link

    def attach_request_response_link_pair(self):
        raise NotImplementedError('Pending')

    def detach_link(self, link, close=False, error=None):
        try:
            self.links[link.name].detach(close=close, error=error)
            del self.links[link.name]
            # TODO check link state before deleting handles
            #del self._input_handles[link.remote_handle]
            del self._output_handles[link.handle]
        except KeyError:
            raise ValueError("No running link that matches input value.")