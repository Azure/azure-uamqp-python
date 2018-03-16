#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import datetime
import uuid

from uamqp import utils
from uamqp import errors
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MessageSender():

    def __init__(self, session, source, target,
                 name=None,
                 send_settle_mode=None,
                 max_message_size=None,
                 link_credit=None,
                 properties=None,
                 debug=False):
        name = name.encode('utf-8') if name else str(uuid.uuid4()).encode('utf-8')
        source = source.encode('utf-8') if isinstance(source, str) else source
        role = constants.Role.Sender

        self.source = c_uamqp.Messaging.create_source(source)
        self.target = target._address.value
        self._conn = session._conn
        self._session = session
        self._link = c_uamqp.create_link(session._session, name, role.value, self.source, self.target)
        self._link.max_message_size = max_message_size

        if link_credit:
            self._link.set_prefetch_count(link_credit)
        if properties:
            self._link.set_attach_properties(utils.data_factory(properties))
        if send_settle_mode:
            self.send_settle_mode = send_settle_mode
        if max_message_size:
            self.max_message_size = max_message_size

        self._sender = c_uamqp.create_message_sender(self._link, self)
        self._sender.set_trace(debug)
        self._state = constants.MessageSenderState.Idle

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self._destroy()

    def _destroy(self):
        self._sender.destroy()
        self._link.destroy()

    def open(self):
        self._sender.open()

    def close(self):
        self._sender.close()

    def send_async(self, message, timeout=0):
        c_message = message.get_message()
        try:
            for data in c_message:
                self._sender.send(data, timeout, message)
        except TypeError:
            self._sender.send(c_message, timeout, message)

    def _state_changed(self, previous_state, new_state):
        try:
            _previous_state = constants.MessageSenderState(previous_state)
        except ValueError:
            _previous_state = new_state
        try:
            _new_state = constants.MessageSenderState(new_state)
        except ValueError:
            _new_state = new_state
        self.on_state_changed(_previous_state, _new_state)

    def on_state_changed(self, previous_state, new_state):
        _logger.debug("Message sender state changed from {} to {}".format(previous_state, new_state))
        self._state = new_state

    @property
    def send_settle_mode(self):
        return self._link.send_settle_mode

    @send_settle_mode.setter
    def send_settle_mode(self, value):
        self._link.send_settle_mode = value.value

    @property
    def max_message_size(self):
        return self._link.max_message_size

    @max_message_size.setter
    def max_message_size(self, value):
        self._link.max_message_size = int(value)
