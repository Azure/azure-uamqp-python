#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uuid
import logging
import time

from .constants import DEFAULT_LINK_CREDIT
from .endpoints import Source
from .link import Link, LinkState, LinkDeliverySettleReason


_LOGGER = logging.getLogger(__name__)


class SenderLink(Link):

    def __init__(self, session, handle, target, **kwargs):
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        role = 'SENDER'
        source = kwargs.pop('source', None) or Source(address="sender-link-{}".format(name))
        super(SenderLink, self).__init__(session, handle, name, role, source, target, **kwargs)

    def _incoming_ATTACH(self, frame):
        super(SenderLink, self)._incoming_ATTACH(frame)
        self.current_link_credit = 0
        self._update_pending_delivery_status()

    def _incoming_FLOW(self, frame):
        rcv_link_credit = frame.link_credit
        rcv_delivery_count = frame.delivery_count
        if rcv_link_credit is None or rcv_delivery_count is None:
            _LOGGER.info("Unable to get link-credit or delivery-count from incoming ATTACH. Detaching link.")
            self._remove_pending_deliveries()
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?
        else:
            self.current_link_credit = rcv_delivery_count + rcv_link_credit - self.delivery_count
            if self.current_link_credit > 0:
                self.send_pending_deliveries()

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
        self._pending_deliveries = {i: d for i, d in self._pending_deliveries.items() if i not in expired}

    def send_pending_deliveries(self):
        pass