#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid

from uamqp import utils
from uamqp import errors
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MessageReceiver():
    """A Message Receiver that opens its own exclsuive Link on an
    existing Session.

    :ivar receive_settle_mode: The mode by which to settle message receive
     operations. If set to `PeekLock`, the receiver will lock a message once received until
     the client accepts or rejects the message. If set to `ReceiveAndDelete`, the service
     will assume successful receipt of the message and clear it from the queue. The
     default is `PeekLock`.
    :vartype receive_settle_mode: ~uamqp.constants.ReceiverSettleMode
    :ivar max_message_size: The maximum allowed message size negotiated for the Link.
    :vartype max_message_size: int

    :param session: The underlying Session with which to receive.
    :type session: ~uamqp.Session
    :param source: The AMQP endpoint to receive from.
    :type source: ~uamqp.Source
    :param target: The name of target (i.e. the client).
    :type target: str or bytes
    :param name: A unique name for the receiver. If not specified a GUID will be used.
    :type name: str or bytes
    :param receive_settle_mode: The mode by which to settle message receive
     operations. If set to `PeekLock`, the receiver will lock a message once received until
     the client accepts or rejects the message. If set to `ReceiveAndDelete`, the service
     will assume successful receipt of the message and clear it from the queue. The
     default is `PeekLock`.
    :type receive_settle_mode: ~uamqp.constants.ReceiverSettleMode
    :param max_message_size: The maximum allowed message size negotiated for the Link.
    :type max_message_size: int
    :param prefetch: The receiver Link credit that determines how many
     messages the Link will attempt to handle per connection iteration.
    :type prefetch: int
    :param properties: Data to be sent in the Link ATTACH frame.
    :type properties: dict
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, session, source, target,
                 on_message_received,
                 name=None,
                 receive_settle_mode=None,
                 max_message_size=None,
                 prefetch=None,
                 properties=None,
                 debug=False,
                 encoding='UTF-8'):
        # pylint: disable=protected-access
        if name:
            self.name = name.encode(encoding) if isinstance(name, str) else name
        else:
            self.name = str(uuid.uuid4()).encode(encoding)
        target = target.encode(encoding) if isinstance(target, str) else target
        role = constants.Role.Receiver

        self.source = source._address.value
        self.target = c_uamqp.Messaging.create_target(target)
        self.on_message_received = on_message_received
        self._conn = session._conn
        self._session = session
        self._link = c_uamqp.create_link(session._session, self.name, role.value, self.source, self.target)

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
        """Open the MessageReceiver in a context manager."""
        self.open()
        return self

    def __exit__(self, *args):
        """Close the MessageReceiver when exiting a context manager."""
        self.destroy()

    def destroy(self):
        """Close both the Receiver and the Link. Clean up any C objects."""
        self._receiver.destroy()
        self._link.destroy()

    def open(self):
        """Open the MessageReceiver in order to start processing messages.

        :raises: ~uamqp.errors.AMQPConnectionError if the Receiver raises
         an error on opening. This can happen if the source URI is invalid
         or the credentials are rejected.
        """
        try:
            self._receiver.open(self.on_message_received)
        except ValueError:
            raise errors.AMQPConnectionError(
                "Failed to open Message Receiver. "
                "Please confirm credentials and target URI.")

    def close(self):
        """Close the Receiver, leaving the link intact."""
        self._receiver.close()

    def _state_changed(self, previous_state, new_state):
        """Callback called whenever the underlying Receiver undergoes a change
        of state. This function wraps the states as Enums to prepare for
        calling the public callback.
        :param previous_state: The previous Receiver state.
        :type previous_state: int
        :param new_state: The new Receiver state.
        :type new_state: int
        """
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
        """Callback called whenever the underlying Receiver undergoes a change
        of state. This function can be overridden.
        :param previous_state: The previous Receiver state.
        :type previous_state: ~uamqp.constants.MessageReceiverState
        :param new_state: The new Receiver state.
        :type new_state: ~uamqp.constants.MessageReceiverState
        """
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
