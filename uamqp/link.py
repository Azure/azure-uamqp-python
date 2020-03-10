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
from io import BytesIO

from ._decode import decode_payload
from ._encode import encode_payload
from .constants import (
    DEFAULT_LINK_CREDIT,
    SessionState,
    SessionTransferState,
    LinkDeliverySettleReason,
    LinkState
)
from .performatives import (
    AttachFrame,
    DetachFrame,
    TransferFrame,
    DispositionFrame,
    FlowFrame,
)

_LOGGER = logging.getLogger(__name__)


class Link(object):
    """

    """

    def __init__(self, session, handle, name, role, source, target, **kwargs):
        self.state = LinkState.DETACHED
        self.name = name or str(uuid.uuid4())
        self.handle = handle
        self.remote_handle = None
        self.role = role
        self.source = source
        self.target = target
        self.link_credit = kwargs.pop('link_credit', None) or DEFAULT_LINK_CREDIT
        self.current_link_credit = self.link_credit
        self.send_settle_mode = kwargs.pop('send_settle_mode', 'MIXED')
        self.rcv_settle_mode = kwargs.pop('rcv_settle_mode', 'FIRST')
        self.unsettled = kwargs.pop('unsettled', None)
        self.incomplete_unsettled = kwargs.pop('incomplete_unsettled', None)
        self.initial_delivery_count = kwargs.pop('initial_delivery_count', 0)
        self.delivery_count = self.initial_delivery_count
        self.received_delivery_id = None
        self.max_message_size = kwargs.pop('max_message_size', None)
        self.remote_max_message_size = None
        self.available = kwargs.pop('available', None)
        self.properties = kwargs.pop('properties', None)
        self.offered_capabilities = None
        self.desired_capabilities = kwargs.pop('desired_capabilities', None)

        self._session = session
        self._is_closed = False
        self._send_links = {}
        self._receive_links = {}
        self._pending_deliveries = {}
        self._received_payload = b""

    def __enter__(self):
        self.attach()
        return self

    def __exit__(self, *args):
        self.detach()

    @classmethod
    def from_incoming_frame(cls, session, handle, frame):
        # check link_create_from_endpoint in C lib
        raise NotImplementedError('Pending')  # TODO: Assuming we establish all links for now...

    def _set_state(self, new_state):
        # type: (LinkState) -> None
        """Update the session state."""
        if new_state is None:
            return
        previous_state = self.state
        self.state = new_state
        _LOGGER.info("Link '%s' state changed: %r -> %r", self.name, previous_state, new_state)

    def _evaluate_status(self):
        if self.current_link_credit <= 0:
            self.current_link_credit = self.link_credit
            self._outgoing_FLOW()

    def _remove_pending_deliveries(self):  # TODO: move to sender
        for delivery in self._pending_deliveries.values():
            delivery.on_settled(LinkDeliverySettleReason.NotDelivered, None)
        self._pending_deliveries = {}
    
    def _on_session_state_change(self):
        if self._session.state == SessionState.MAPPED:
            if not self._is_closed and self.state == LinkState.DETACHED:
                self._outgoing_ATTACH()
                self._set_state(LinkState.ATTACH_SENT)
        elif self._session.state == SessionState.DISCARDING:
            self._remove_pending_deliveries()
            self._set_state(LinkState.DETACHED)

    def _outgoing_ATTACH(self):
        self.delivery_count = self.initial_delivery_count
        attach_frame = AttachFrame(
            name=self.name,
            handle=self.handle,
            role=self.role,
            send_settle_mode=self.send_settle_mode,
            rcv_settle_mode=self.rcv_settle_mode,
            source=self.source,
            target=self.target,
            #unsettled=self.unsettled,
            #incomplete_unsettled=self.incomplete_unsettled,
            initial_delivery_count=self.initial_delivery_count if self.role == 'SENDER' else None,
            max_message_size=self.max_message_size,
            offered_capabilities=self.offered_capabilities if self.state == LinkState.ATTACH_RCVD else None,
            desired_capabilities=self.desired_capabilities if self.state == LinkState.DETACHED else None,
            properties=self.properties
        )
        self._session._outgoing_ATTACH(attach_frame)

    def _incoming_ATTACH(self, frame):
        if self._is_closed:
            raise ValueError("Invalid link")
        elif not frame.source or not frame.target:  # TODO: not sure if we should check here
            _LOGGER.info("Cannot get source or target. Detaching link")
            self._remove_pending_deliveries()
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?
            raise ValueError("Invalid link")
        self.remote_handle = frame.handle
        self.remote_max_message_size = frame.max_message_size
        self.offered_capabilities = frame.offered_capabilities
        if self.properties:
            self.properties.update(frame.properties)
        else:
            self.properties = frame.properties
        if self.state == LinkState.DETACHED:
            self._set_state(LinkState.ATTACH_RCVD)
        elif self.state == LinkState.ATTACH_SENT:
            self._set_state(LinkState.ATTACHED)
    
    def _outgoing_FLOW(self):
        flow_frame = FlowFrame(
            handle=self.handle,
            delivery_count=self.delivery_count,
            link_credit=self.current_link_credit,
            # available=
            # drain=
            # echo=
            # properties=
        )
        self._session._outgoing_FLOW(flow_frame)

    def _incoming_FLOW(self, frame):
        pass

    def _outgoing_DETACH(self, close=False, error=None):
        detach_frame = DetachFrame(handle=self.handle, closed=close, error=error)
        self._session._outgoing_DETACH(detach_frame)
        if close:
            self._is_closed = True

    def _incoming_DETACH(self, frame):
        if self.state == LinkState.ATTACHED:
            self._outgoing_DETACH(close=frame.closed)
        elif frame.closed and not self._is_closed and self.state in [LinkState.ATTACH_SENT, LinkState.ATTACH_RCVD]:
            # Received a closing detach after we sent a non-closing detach.
            # In this case, we MUST signal that we closed by reattaching and then sending a closing detach.
            self._outgoing_ATTACH()
            self._outgoing_DETACH(close=True)
        self._remove_pending_deliveries()
        # TODO: on_detach_hook
        if frame.error:
            self._set_state(LinkState.ERROR)
        else:
            self._set_state(LinkState.DETACHED)

    def attach(self):
        if self._is_closed:
            raise ValueError("Link already closed.")
        self._outgoing_ATTACH()
        self._set_state(LinkState.ATTACH_SENT)
        self._received_payload = b''

    def detach(self, close=False, error=None):
        if self._is_closed:
            raise ValueError("Link already closed.")
        self._remove_pending_deliveries()  # TODO: Keep?
        if self.state in [LinkState.ATTACH_SENT, LinkState.ATTACH_RCVD]:
            self._outgoing_DETACH(close=close, error=error)
            self._set_state(LinkState.DETACHED)
        elif self.state == LinkState.ATTACHED:
            self._outgoing_DETACH(close=close, error=error)
            self._set_state(LinkState.ATTACH_SENT)
