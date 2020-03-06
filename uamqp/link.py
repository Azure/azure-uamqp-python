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

from .constants import DEFAULT_LINK_CREDIT
from .performatives import (
    AttachFrame,
    DetachFrame,
    TransferFrame,
    FlowFrame,
)

LOGGER = logging.getLogger(__name__)


class LinkDeliverySettleReason(Enum):

    DispositionReceived = 0
    Settled = 1
    NotDelivered = 2
    Timeout = 3
    Cancelled = 4


class LinkState(Enum):

    DETACHED = 0
    ATTACH_SENT = 1
    ATTACH_RCVD = 2
    ATTACHED = 3
    ERROR = 4


class Link(object):
    """

    """

    def __init__(self, handle, name, role, source, target, **kwargs):
        self.state = LinkState.DETACHED
        self.name = name or str(uuid.uuid4())
        self.handle = handle
        self.role = role
        self.source = source
        self.target = target
        self.link_credit = kwargs.pop('link_credit', None) or DEFAULT_LINK_CREDIT
        self.send_settle_mode = kwargs.pop('send_settle_mode', 'MIXED')
        self.rcv_settle_mode = kwargs.pop('rcv_settle_mode', 'FIRST')
        self.unsettled = kwargs.pop('unsettled', None)
        self.incomplete_unsettled = kwargs.pop('incomplete_unsettled', None)
        self.initial_delivery_count = kwargs.pop('initial_delivery_count', 0)
        self.delivery_count = self.initial_delivery_count
        self.max_message_size = kwargs.pop('max_message_size', None)

        self.remote_handle = kwargs.pop('remote_handle', None)

        self._send_links = {}
        self._receive_links = {}
        self._outgoing_frames = queue.Queue()

        self._on_receive_attach_frame = kwargs.pop('attach_frame_hook', None)
        self._on_receive_detach_frame = kwargs.pop('detach_frame_hook', None)

        self.properties = kwargs.pop('properties', None) or kwargs

    def __enter__(self):
        self.attach()
        return self

    def __exit__(self, *args):
        self.detach()

    @classmethod
    def from_incoming_frame(cls, handle, frame):
        if not isinstance(frame, AttachFrame):
            raise TypeError("Invalid frame received on handle with no link: {}".format(frame))
        raise NotImplementedError('Pending')  # TODO: Assuming we establish all links for now...

    def _set_state(self, new_state):
        # type: (LinkState) -> None
        """Update the session state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        print("Link '{}' state changed: {} -> {}".format(self.name, previous_state, new_state))

    def _can_read(self):
        # type: () -> bool
        """Whether the session is in a state where it is legal to read for incoming frames."""
        return True

    def _can_write(self):
        # type: () -> bool
        """Whether the session is in a state where it is legal to write outgoing frames."""
        return True

    def _process_incoming_frame(self, frame):
        # type: (int, Performative) -> None
        if isinstance(frame, AttachFrame):
            if frame.source and frame.target:
                self.remote_handle = frame.handle
                self.max_message_size = frame.max_message_size
                self.offered_capabilities = frame.offered_capabilities
                self.properties.update(frame.properties)
                flow_frame = FlowFrame(
                    handle=self.handle,
                    delivery_count=self.delivery_count,
                    link_credit=self.link_credit,
                )
                self._outgoing_frames.put((flow_frame))
            else:
                print("Link is error state")
        # if channel not in self.incoming_endpoints:
        #     self.incoming_endpoints[channel] = Session.from_incoming_frame(frame)
        # else:
        #     self.incoming_endpoints[channel].incoming_frame(frame)

    def _is_outgoing_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a frame can legally be sent, and if so, whether
        the successful sending of that frame will result in a change of state.
        """
        return True

    def _is_incoming_frame_legal(self, frame):  # pylint: disable=too-many-return-statements
        # type: (Performative) -> Tuple(bool, Optional[ConnectionState])
        """Determines whether a received frame is legal, and if so, whether
        it results in a change of session state.
        """
        return True

    def incoming_frame(self, frame):
        if self._can_read:
            if self._is_incoming_frame_legal(frame):
                self._process_incoming_frame(frame)
            else:
                raise TypeError("Received illegal frame {} in current state.".format(type(frame)))

    def outgoing_frame(self):
        if not self._can_write:
            return None
        frame = self._outgoing_frames.get_nowait()
        if self._is_outgoing_frame_legal(frame):
            #self.delivery_count += 1
            return frame
        raise TypeError("Attempt to send frame {} in illegal state.".format(type(frame)))

    def attach(self, **kwargs):
        attach_frame = kwargs.get('attach_frame') or AttachFrame(
            name=self.name,
            handle=self.handle,
            role=self.role,
            send_settle_mode=self.send_settle_mode,
            rcv_settle_mode=self.rcv_settle_mode,
            source=self.source,
            target=self.target,
            unsettled=self.unsettled,
            incomplete_unsettled=self.incomplete_unsettled,
            initial_delivery_count=self.initial_delivery_count,
            max_message_size=self.max_message_size,
            properties=self.properties
        )
        self._outgoing_frames.put((attach_frame))

    def detach(self, closed=False, error=None):
        detach_frame = DetachFrame(handle=self.handle, closed=closed, error=error)
        self._outgoing_frames.put(detach_frame)

    def send_message(self, message):
        transfer_frame = TransferFrame(
            _payload=message,
            handle=self.handle,
            delivery_tag=bytes(self.delivery_count),
            message_format=message.FORMAT,
            settled=False,
            more=False,
        )
        self._outgoing_frames.put(transfer_frame)
        self.delivery_count += 1
