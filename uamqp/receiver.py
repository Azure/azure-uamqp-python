#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uuid
import logging
from io import BytesIO

from ._decode import decode_payload
from .constants import DEFAULT_LINK_CREDIT
from .endpoints import Target
from .link import Link
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


class ReceiverLink(Link):

    def __init__(self, session, handle, source, **kwargs):
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        role = 'RECEIVER'
        target = kwargs.pop('target', None) or Target(address="receiver-link-{}".format(name))
        super(ReceiverLink, self).__init__(session, handle, name, role, source, target, **kwargs)
        self.on_message_received = kwargs.get('on_message_received')
        self.on_transfer_received = kwargs.get('on_transfer_received')
        if not self.on_message_received and not self.on_transfer_received:
            raise ValueError("Must specify either a message or transfer handler.")

    def _process_incoming_message(self, frame, message):
        try:
            if self.on_message_received:
                return self.on_message_received(message)
            elif self.on_transfer_received:
                return self.on_transfer_received(frame, message)
        except Exception as e:
            _LOGGER.error("Handler function failed with error: %r", e)
        return None

    def _incoming_attach(self, frame):
        super(ReceiverLink, self)._incoming_attach(frame)
        if frame.initial_delivery_count is None:
            _LOGGER.info("Cannot get initial-delivery-count. Detaching link")
            self._remove_pending_deliveries()
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?
        self.delivery_count = frame.initial_delivery_count
        self.current_link_credit = self.link_credit
        self._outgoing_FLOW()

    def _incoming_transfer(self, frame):
        self.current_link_credit -= 1
        self.delivery_count += 1
        self.received_delivery_id = frame.delivery_id
        if not self.received_delivery_id and not self._received_payload:
            pass  # TODO: delivery error
        if self._received_payload or frame.more:
            self._received_payload += frame.payload  # TODO: Fix multi-part messages
        if not frame.more:
            payload_data = self._received_payload or frame.payload
            delivery_state = self._process_incoming_message(frame, payload_data)
            if not frame.settled and delivery_state:
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

    def send_disposition(self, delivery_id, delivery_state=None):
        if self._is_closed:
            raise ValueError("Link already closed.")
        self._outgoing_DISPOSITION(delivery_id, delivery_state)
