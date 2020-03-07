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
from urllib.parse import urlparse
from enum import Enum
from io import BytesIO

from ._decode import decode_payload
from ._encode import encode_payload
from .constants import DEFAULT_LINK_CREDIT
from .performatives import (
    AttachFrame,
    DetachFrame,
    TransferFrame,
    DispositionFrame,
    FlowFrame,
)

_LOGGER = logging.getLogger(__name__)


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

class PendingDelivery(object):

    def __init__(self, **kwargs):
        self.message = kwargs.get('message')
        self.frame = None
        self.on_delivery_settled = kwargs.get('on_delivery_settled')
        self.link = kwargs.get('link')
        self.start = time.time()
        self.transfer_state = None
        self.timeout = kwargs.get('timeout')
    
    def on_settled(self, reason, state):
        if self.on_delivery_settled:
            try:
                self.on_delivery_settled(self.message, reason, state)
            except Exception as e:
                _LOGGER.warning("Message 'on_send_complete' callback failed: {}".format(e))


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
        self._outgoing_frames = queue.Queue()
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
        _LOGGER.info("Link '{}' state changed: {} -> {}".format(self.name, previous_state, new_state))

    def _remove_pending_deliveries(self):
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
        elif self._session.state == SessionState.ERROR:
            self._remove_pending_deliveries()
            self._set_state(LinkState.ERROR)

    def _process_incoming_message(self, message):
        return None  # return delivery state

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
            initial_delivery_count=self.initial_delivery_count is self.role == 'SENDER' else None,
            max_message_size=self.max_message_size,
            offered_capabilities=self.offered_capabilities if self.state == LinkState.ATTACH_RCVD else None,
            desired_capabilities=self.desired_capabilities if self.state == LinkState.DETACHED else None,
            properties=self.properties
        )
        self._session._outgoing_ATTACH(attach_frame)

    def _incoming_ATTACH(self, frame):
        if not frame.source or not frame.target:  # TODO: not sure if we should check here
            _LOGGER.info("Cannot get source or target. Detaching link")
            self._remove_pending_deliveries()
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?

        self.remote_handle = frame.handle
        self.remote_max_message_size = frame.max_message_size
        self.offered_capabilities = frame.offered_capabilities
        self.properties.update(frame.properties)
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

    def _outgoing_TRANSFER(self, delivery):
        delivery_count = self.delivery_count + 1
        settled=self.send_settle_mode != 'UNSETTLED'
        delivery.frame = TransferFrame(
            handle=self.handle,
            delivery_tag=bytes(delivery_count),
            message_format=delivery.message.FORMAT,
            settled=settled,
            more=False,
            _payload=encode_payload(b"", delivery.message)
        )
        self._session._outgoing_TRANSFER(delivery)
        if delivery.transfer_state == SessionTransferState.Okay:
            self.delivery_count = delivery_count
            self.current_link_credit -= 1
            if settled:  # TODO: what about the MIXED mode?
                delivery.on_settled(LinkDeliverySettleReason.settled, None)
            else:
                self._pending_deliveries[delivery.id] = delivery

    def _incoming_TRANSFER(self, frame):
        self.current_link_credit -= 1
        self.delivery_count += 1
        self.received_delivery_id = frame.delivery_id
        if not self.received_delivery_id and not self._received_payload:
            pass  # TODO: delivery error
        if self._received_payload or frame.more:
            self._received_payload += frame._payload
        if not frame.more:
            payload_data = self._received_payload or frame._payload
            byte_buffer = BytesIO(payload_data)
            decoded_message = decode_payload(byte_buffer, length=len(payload_data))
            delivery_state = self._process_incoming_message(decoded_message)
            if delivery_state:
                self._outgoing_DISPOSITION(frame.delivery_id, delivery_state)

    def _outgoing_DISPOSITION(self, delivery_id, delivery_state):
        disposition_frame = DispositionFrame(
            role=self.role,
            first=delivery_id,
            last=delivery_id,
            settled=True,
            state=delivery_state,
            # batchable=
        )
        self._session._outgoing_DISPOSITION(disposition_frame)

    def _incoming_DISPOSITION(self, frame):
        if not frame.settled:
            return
        range_end = (frame.last or frame.first) + 1
        settled_ids = [i for i in range(frame.first, range_end)]
        remove = {id: d for id, d in self._pending_deliveries.items() if id in settled_ids}
        for delivery_id, delivery in remove.items():
            self._pending_deliveries.pop(delivery_id)
            delivery.on_settled(LinkDeliverySettleReason.DispositionReceived, frame.state)

    def _outgoing_DETACH(self, close=False, error=None):
        detach_frame = DetachFrame(handle=self.handle, closed=close, error=error)
        self._session._outgoing_DETACH(detach_frame)
        if close:
            self._is_closed = True

    def _incoming_DETACH(self, frame):
        if self.state == LinkState.ATTACHED:
            self._outgoing_DETACH(close=frame.closed)
        else if frame.close and not self._is_closed and self.state in [LinkState.ATTACH_SENT, LinkState.ATTACH_RCVD]:
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

    def _update_pending_delivery_status(self):
        now = time.time()
        if self.current_link_credit <= 0:
            self.current_link_credit = self.link_credit
            self._outgoing_FLOW()
        expired = []
        for delivery in self._pending_deliveries.values():
            if delivery.timeout and (delivery.start - now) >= delivery.timeout:
                expired.append(delivery.id)
                delivery.on_settled(LinkDeliverySettleReason.Timeout, None)
        self._pending_deliveries = {i: d for i, d in self._pending_deliveries if i not if expired}

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

    def send_transfer(self, message, **kwargs):
        if self._is_closed:
            raise ValueError("Link already closed.")
        if self.state != LinkState.ATTACHED:
            raise ValueError("Link is not attached.")
        if self.current_link_credit == 0:
            raise ValueError("Link is busy (no available credit).")
        delivery = PendingDelivery(
            on_delivery_settled=kwargs.get('on_send_complete'),
            timeout=kwargs.get('timeout')
            link=self,
            message=message,
        )
        self._outgoing_TRANSFER(delivery)
        return delivery.frame.delivery_id
    
    def cancel_transfer(self, delivery_id):
        try:
            delivery = self._pending_deliveries.pop(delivery_id)
            delivery.on_settled(LinkDeliverySettleReason.Cancelled, None)
        except KeyError:
            raise ValueError("No pending delivery with ID '{}' found.".format(delivery_id))

    def send_disposition(self, delivery_id, delivery_state=None):
        if self._is_closed:
            raise ValueError("Link already closed.")
        self._outgoing_DISPOSITION(delivery_id, delivery_state)
