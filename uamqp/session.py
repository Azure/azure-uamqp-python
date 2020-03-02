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
from urllib.parse import urlparse
from enum import Enum

from .constants import INCOMING_WINDOW, OUTGOING_WIDNOW
from .performatives import (
    BeginFrame,
    EndFrame,
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
        self.state = SessionState.UNMAPPED
        self.channel = channel

        self.remote_channel = kwargs.pop('remote_channel', None)
        self.next_outgoing_id = kwargs.pop('next_outgoing_id', 0)
        self.incoming_window = kwargs.pop('incoming_window', INCOMING_WINDOW)
        self.outgoing_window = kwargs.pop('outgoing_window', OUTGOING_WIDNOW)
        self.handle_max = kwargs.get('handle_max', None)
        self.offered_capabilities = kwargs.pop('offered_capabilities', None)
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)

        self.current_transfer_id = None
        self.remote_incoming_window = kwargs.pop('remote_incoming_window', None)
        self.remote_outgoing_window = kwargs.pop('remote_outgoing_window', None)
        self.links = {}
        self._outgoing_frames = queue.Queue()

        self._on_receive_begin_frame = kwargs.pop('begin_frame_hook', None)
        self._on_receive_end_frame = kwargs.pop('end_frame_hook', None)

        self.properties = kwargs.pop('properties', None) or kwargs

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, *args):
        self.end()

    @classmethod
    def from_incoming_frame(cls, channel, frame):
        if not isinstance(frame, BeginFrame):
            raise TypeError("Frame received on channel with no Session: {}".format(frame))
        session = cls(
            channel,
            remote_channel=frame.remote_channel,
            next_outgoing_id=frame.next_outgoing_id,
            remote_incoming_window=frame.incoming_window,
            remote_outgoing_window=frame.outgoing_window,
            handle_max=frame.handle_max,
            offered_capabilities=frame.offered_capabilities,
            desired_capabilities=frame.desired_capabilities)
        session.state = SessionState.BEGIN_RCVD
        return session

    def _set_state(self, new_state):
        # type: (SessionState) -> None
        """Update the session state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        print("Session state changed: {} -> {}".format(previous_state, new_state))

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

    def _process_incoming_frame(self, frame):
        # type: (int, Performative) -> None
        if isinstance(frame, BeginFrame):
            self.remote_channel = frame.remote_channel
        # if channel not in self.incoming_endpoints:
        #     self.incoming_endpoints[channel] = Session.from_incoming_frame(frame)
        # else:
        #     self.incoming_endpoints[channel].incoming_frame(frame)

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

    def incoming_frame(self, frame):
        if self._can_read:
            legal, new_state = self._is_incoming_frame_legal(frame)
            if legal:
                self._set_state(new_state)
                self._process_incoming_frame(frame)
            else:
                raise TypeError("Received illegal frame {} in current state {}".format(type(frame), self.state))

    def outgoing_frame(self):
        if not self._can_write:
            return None
        frame = self._outgoing_frames.get_nowait()
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
