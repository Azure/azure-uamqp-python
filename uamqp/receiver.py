#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uuid
import logging

from .constants import DEFAULT_LINK_CREDIT
from .endpoints import Target
from .link import Link, LinkState, LinkDeliverySettleReason
from .performatives import (
    FlowFrame
)


_LOGGER = logging.getLogger(__name__)


class ReceiverLink(Link):

    def __init__(self, session, handle, source, **kwargs):
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        role = 'RECEIVER'
        target = kwargs.pop('target', None) or Target(address="receiver-link-{}".format(name))
        super(ReceiverLink, self).__init__(session, handle, name, role, source, target, **kwargs)

    def _incoming_ATTACH(self, frame):
        super(ReceiverLink, self)._incoming_ATTACH(frame)
        if not frame.initial_delivery_count:
            _LOGGER.info("Cannot get initial-delivery-count. Detaching link")
            self._remove_pending_deliveries(True)
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?
        self.delivery_count = frame.initial_delivery_count
        self.current_link_credit = self.link_credit
        self._outgoing_FLOW()

    def send_transfer(self, message):
        raise TypeError("Link is not a SenderLink")
        