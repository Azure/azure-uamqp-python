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
from .link import Link
from .performatives import (
    BeginFrame,
    EndFrame,
    FlowFrame,
    AttachFrame,
    TransferFrame,
    DispositionFrame
)


DEFAULT_LINK_CREDIT = 1000
LOGGER = logging.getLogger(__name__)


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

    def __init__(self, channel, **kwargs):
        self.name = kwargs.pop('name', None) or str(uuid.uuid4())
        self.state = SessionState.UNMAPPED
        self.handle_max = kwargs.get('handle_max', None)
        self.properties = kwargs.pop('properties', None)
        self.channel = channel
        self.remote_channel = None
        self.next_outgoing_id = kwargs.pop('next_outgoing_id', 0)
        self.next_incoming_id = None
        self.target_incoming_window = kwargs.pop('incoming_window', INCOMING_WINDOW)
        self.target_outgoing_window = kwargs.pop('outgoing_window', OUTGOING_WIDNOW)
        self.incoming_window = self.target_incoming_window
        self.outgoing_window = self.target_outgoing_window
        self.remote_incoming_window = None
        self.remote_outgoing_window = None
        self.offered_capabilities = None
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)

        self.links = {}
        self._output_handles = {}
        self._input_handles = {}
        self._outgoing_frames = queue.Queue()
        self._on_receive_begin_frame = kwargs.pop('begin_frame_hook', None)
        self._on_receive_end_frame = kwargs.pop('end_frame_hook', None)

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, *args):
        self.end()

    @classmethod
    def from_incoming_frame(cls, channel, frame):
        raise NotImplementedError()

    def _set_state(self, new_state):
        # type: (SessionState) -> None
        """Update the session state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        print("Session '{}' state changed: {} -> {}".format(self.name, previous_state, new_state))

    def _can_read(self):
        # type: () -> bool
        """Whether the session is in a state where it is legal to read for incoming frames."""
        return self.state in (SessionState.BEGIN_RCVD, SessionState.MAPPED, SessionState.END_SENT)

    def _can_write(self):
        # type: () -> bool
        """Whether the session is in a state where it is legal to write outgoing frames."""
        return self.state in (
            SessionState.BEGIN_SENT,
            SessionState.MAPPED,
            SessionState.END_RCVD,
        )

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

    def _process_incoming_frame(self, frame):
        # type: (int, Performative) -> None
        if isinstance(frame, TransferFrame):
            self.next_incoming_id += 1
            self.remote_outgoing_window -= 1
            self.incoming_window -= 1
            self._input_handles[frame.handle].incoming_frame(frame)
        elif isinstance(frame, DispositionFrame):
            for handle in self._input_handles.values():
                handle.incoming_frame(frame)
        elif isinstance(frame, BeginFrame):
            self.remote_channel = frame.remote_channel
            self.handle_max = frame.handle_max
            self.next_incoming_id = frame.next_outgoing_id
            self.remote_incoming_window = frame.incoming_window
            self.remote_outgoing_window = frame.outgoing_window
        elif isinstance(frame, AttachFrame):
            self._input_handles[frame.handle] = self.links[frame.name]
            self._input_handles[frame.handle].incoming_frame(frame)
        elif isinstance(frame, FlowFrame):
            self.next_incoming_id = frame.next_outgoing_id
            self.next_outgoing_id = frame.next_incoming_id
            self.remote_incoming_window = frame.incoming_window
            self.remote_outgoing_window = frame.outgoing_window
            if frame.handle:
                self._input_handles[frame.handle].incoming_frame(frame)
        elif isinstance(frame, EndFrame):
            return # TODO process end
        else:
            print("Unrecognized frame: ", frame)

    def _is_outgoing_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a frame can legally be sent, and if so, whether
        the successful sending of that frame will result in a change of state.
        """
        if self.state == SessionState.UNMAPPED:
            return isinstance(frame, BeginFrame), SessionState.BEGIN_SENT
        if self.state == SessionState.BEGIN_SENT:
            return True, None
        if self.state == SessionState.BEGIN_RCVD:
            return isinstance(frame, BeginFrame), SessionState.MAPPED
        if self.state == SessionState.MAPPED:
            if isinstance(frame, EndFrame):
                return True, SessionState.DISCARDING if frame.error else SessionState.END_SENT
            return True, None
        if self.state == SessionState.END_RCVD:
            return True, SessionState.UNMAPPED if isinstance(frame, EndFrame) else None
        return False, None

    def _is_incoming_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a received frame is legal, and if so, whether
        it results in a change of session state.
        """
        if self.state == SessionState.BEGIN_SENT:
            return isinstance(frame, BeginFrame), SessionState.MAPPED
        if self.state == SessionState.BEGIN_RCVD:
            return True, None
        if self.state == SessionState.MAPPED:
            return True, SessionState.END_RCVD if isinstance(frame, EndFrame) else None
        if self.state == SessionState.END_SENT:
            return True, SessionState.UNMAPPED if isinstance(frame, EndFrame) else None
        return False, None

    def _get_one_outgoing_frame(self):  # TODO: ouch
        if not self._can_write:
            return None
        frame = None
        try:
            frame = self._outgoing_frames.get_nowait()
        except queue.Empty:
            print("no session frames, checking links")
            for link in self.links.values():
                try:
                    frame = link.outgoing_frame()
                    if frame:
                        print("found outgoing link frame")
                        break
                except queue.Empty as e:
                    frame = e
        try:
            raise frame
        except TypeError:
            return frame

    def incoming_frame(self, frame):
        if self._can_read:
            legal, new_state = self._is_incoming_frame_legal(frame)
            if legal:
                self._set_state(new_state)
                self._process_incoming_frame(frame)
            else:
                raise TypeError("Received illegal frame {} in current state {}".format(type(frame), self.state))

    def outgoing_frame(self):
        frame = self._get_one_outgoing_frame()
        if not frame:
            return None
        elif isinstance(frame, TransferFrame):
            frame.delivery_id = self.next_outgoing_id
            self.next_outgoing_id += 1
            self.remote_incoming_window -= 1
            self.outgoing_window -= 1
        elif isinstance(frame, FlowFrame):
            frame.next_incoming_id = self.next_incoming_id
            frame.incoming_window = self.incoming_window
            frame.next_outgoing_id = self.next_outgoing_id
            frame.outgoing_window = self.outgoing_window
        legal, new_state = self._is_outgoing_frame_legal(frame)
        if legal:
            self._set_state(new_state)
            return frame
        raise TypeError("Attempt to send frame {} in illegal state {}".format(type(frame), self.state))

    def begin(self, **kwargs):
        begin_frame = kwargs.get('begin_frame') or BeginFrame(
            remote_channel=self.remote_channel,
            next_outgoing_id=self.next_outgoing_id,
            outgoing_window=self.outgoing_window,
            incoming_window=self.incoming_window,
            handle_max=self.handle_max,
            offered_capabilities=self.offered_capabilities,
            desired_capabilities=self.desired_capabilities,
            properties=self.properties,
        )
        self._outgoing_frames.put((begin_frame))

    def end(self, error=None):
        end_frame = EndFrame(error=error)
        self._outgoing_frames.put(end_frame)

    def attach_receiver_link(self, **kwargs):
        assigned_handle = self._get_next_output_handle()
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        link = Link(
            handle=assigned_handle,
            name=name,
            role='RECEIVER',
            initial_delivery_count=None,
            target=kwargs.pop('target', None) or Target(address="receiver-link-{}".format(name)),
            **kwargs)
        self.links[name] = link
        self._output_handles[assigned_handle] = link
        link.attach()
        return link

    def attach_sender_link(self, **kwargs):
        assigned_handle = self._get_next_output_handle()
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        link = Link(
            handle=assigned_handle,
            name=name,
            role='SENDER',
            source=kwargs.pop('source', None) or Source(address="sender-link-{}".format(name)),
            **kwargs)
        self._output_handles[assigned_handle] = link
        self.links[name] = link
        link.attach()
        return link

    def attach_request_response_link_pair(self):
        raise NotImplementedError('Pending')

    def detach_link(self, link, error=None):
        try:
            self.links[link.name].detach(error=error)
        except KeyError:
            raise ValueError("No running link that matches input value.")