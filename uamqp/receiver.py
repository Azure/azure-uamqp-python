#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import datetime
import queue
import uuid

import uamqp
from uamqp import utils
from uamqp import errors
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MessageReceiver():

    def __init__(self, session, source, target,
                 name=None,
                 receive_settle_mode=None,
                 max_message_size=None,
                 prefetch=None,
                 properties=None,
                 debug=False):
        name = name.encode('utf-8') if name else str(uuid.uuid4()).encode('utf-8')
        target = target.encode('utf-8') if isinstance(target, str) else target
        role = constants.Role.Receiver
        
        self.source = source._address.value
        self.target = c_uamqp.Messaging.create_target(target)
        self._conn = session._conn
        self._session = session
        self._link = c_uamqp.create_link(session._session, name, role.value, self.source, self.target)

        if prefetch:
            self._link.set_prefetch_count(prefetch)
        if properties:
            self._link.set_attach_properties(utils.data_factory(properties))
        if receive_settle_mode:
            self.receive_settle_mode = receive_settle_mode
        if max_message_size:
            self.max_message_size = max_message_size

        self._receiver = c_uamqp.create_message_receiver(self._link, self)
        self._receiver.set_trace(debug)
        self._state = constants.MessageReceiverState.Idle

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self._destroy()

    def _destroy(self):
        self._receiver.destroy()
        self._link.destroy()

    def open(self, on_message_received):
        self._receiver.open(on_message_received)

    def close(self):
        self._receiver.close()

    def _state_changed(self, previous_state, new_state):
        try:
            _previous_state = constants.MessageReceiverState(previous_state)
        except ValueError:
            _previous_state = new_state
        try:
            _new_state = constants.MessageReceiverState(new_state)
        except ValueError:
            _new_state = new_state
        self.on_state_changed(_previous_state, _new_state)

    def on_state_changed(self, previous_state, new_state):
        if new_state != previous_state:
            _logger.debug("Message receiver state changed from {} to {}".format(previous_state, new_state))
            self._state = new_state

    @property
    def receive_settle_mode(self):
        return self._link.receive_settle_mode

    @receive_settle_mode.setter
    def receive_settle_mode(self, value):
        self._link.receive_settle_mode = value.value

    @property
    def max_message_size(self):
        return self._link.max_message_size

    @max_message_size.setter
    def max_message_size(self, value):
        self._link.max_message_size = int(value)

