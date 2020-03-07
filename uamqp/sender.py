#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uuid
import logging

from .constants import DEFAULT_LINK_CREDIT
from .endpoints import Source
from .link import Link, LinkState, LinkDeliverySettleReason


_LOGGER = logging.getLogger(__name__)


class SenderLink(Link):

    def __init__(self, session, handle, target, **kwargs):
        name = kwargs.pop('name', None) or str(uuid.uuid4())
        role = 'SENDER'
        source = kwargs.pop('source', None) or Source(address="sender-link-{}".format(self.name))
        super(SenderLink, self).__init__(session, handle, name, role, source, target, **kwargs)

    def _incoming_ATTACH(self, frame):
        super(SenderLink, self)._incoming_ATTACH(frame)
        self.current_link_credit = 0

    def _incoming_FLOW(self, frame):
        rcv_link_credit = frame.link_credit
        rcv_delivery_count = frame.delivery_count
        if not rcv_link_credit or not rcv_delivery_count:
            _LOGGER.info("Unable to get link-credit or delivery-count from incoming ATTACH. Detaching link.")
            self._remove_pending_deliveries(True)
            self._set_state(LinkState.DETACHED)  # TODO: Send detach now?
        else:
            self.current_link_credit = rcv_delivery_count + rcv_link_credit - self.delivery_count
            if self.current_link_credit > 0:
                self.send_pending_deliveries()

    def send_pending_deliveries(self):
        pass