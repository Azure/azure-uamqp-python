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

from .endpoints import Source, Target
from .constants import (
    DEFAULT_LINK_CREDIT,
    SessionState,
    SessionTransferState,
    ManagementLinkState,
    LinkDeliverySettleReason,
    LinkState,
    Role,
    SenderSettleMode,
    ReceiverSettleMode
)
from .performatives import (
    AttachFrame,
    DetachFrame,
    TransferFrame,
    DispositionFrame,
    FlowFrame,
)

_LOGGER = logging.getLogger(__name__)


class ManagementLink(object):
    """

    """
    def __init__(self, session, endpoint):
        self.next_message_id = 0
        self.state = ManagementLinkState.IDLE
        self._pending_operations = []
        self._session = session
        self._request_link = session.create_sender_link(
            endpoint, on_link_state_change=self._on_sender_state_change)
        self._response_link = session.create_receiver_link(
            endpoint, on_link_state_change=self._on_receiver_state_change)

    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def _set_state(self, new_state):

    
    def _on_sender_state_change(self, previous_state, new_state):
        if new_state == previous_state:
            return
        if self.state == ManagementLinkState.OPENING:
            if new_state == LinkState.OPENING:
        elif self.state == ManagementLinkState.OPEN:
        elif self.state == ManagementLinkState.CLOSING:
            if new_state not in [LinkState.DETACHED, LinkState.DETACH_RECEIVED]:
                self._set_state(ManagementLinkState.ERROR)
        elif self.state == ManagementLinkState.ERROR:
            # All state transitions shall be ignored.
            return
    
    def open(self):
        if self.state != ManagementLinkState.IDLE:
            raise ValueError("Management links are already open or opening.")
        self.state = ManagementLinkState.OPENING
        self.response_link.attach()
        self.request_link.attach()
    
    def close(self):
        if self.state != ManagementLinkState.IDLE:
            self.response_link.detach(close=True)
            self.request_link.detach(close=True)
            self._pending_operations = []
        self.state == ManagementLinkState.IDLE