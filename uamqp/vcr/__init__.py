#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import uuid
import json

import uamqp

directory = "C:\\Users\\antisch\\Documents\\GitHub\\azure-uamqp-python\\samples\\recordings"
filename = "test_recording.txt"

def _record_event(event_type, data):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    recording = os.path.join(directory, filename)
    with open(recording, 'a') as recording_data:
        json_frame = {event_type: data}
        json.dump(json_frame, recording_data)
        recording_data.write("\n")


class Message(uamqp.message.Message):
    """An AMQP message. This message supports recording and playback
    for test suites.

    When sending, depending on the nature of the data,
    different body encoding will be used. If the data is str or bytes,
    a single part DataBody will be sent. If the data is a list or str/bytes,
    a multipart DataBody will be sent. Any other type of list will be sent
    as a SequenceBody, where as any other type of data will be sent as
    a ValueBody. An empty payload will also be sent as a ValueBody.

    :ivar on_send_complete: A custom callback to be run on completion of
     the send operation of this message. The callback must take two parameters,
     a result (of type ~uamqp.constants.MessageSendResult) and an error (of type
     Exception). The error parameter may be None if no error ocurred or the error
     information was undetermined.
    :vartype on_send_complete: callable[~uamqp.constants.MessageSendResult, Exception]

    :param body: The data to send in the message.
    :type body: Any Python data type.
    :param properties: Properties to add to the message.
    :type properties: ~uamqp.message.MessageProperties
    :param application_properties: Service specific application properties.
    :type application_properties: dict
    :param annotations: Service specific message annotations. Keys in the dictionary
     must be ~uamqp.types.AMQPSymbol or ~uamqp.types.AMQPuLong.
    :type annotations: dict
    :param msg_format: A custom message format. Default is 0.
    :type msg_format: int
    :param message: Internal only. This is used to wrap an existing message
     that has been received from an AMQP service. If specified, all other
     parameters will be ignored.
    :type message: ~uamqp.c_uamqp.cMessage
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, *args, **kwargs):
        self._request_id = str(uuid.uuid4())
        super(Message, self).__init__(*args, **kwargs)


    def _on_message_sent(self, result, error=None):
        """Callback run on a message send operation. If message
        has a user defined callback, it will be called here. If the result
        of the operation is failure, the message state will be reverted
        to 'pending' up to the maximum retry count.

        :param result: The result of the send operation.
        :type result: int
        :param error: An Exception if an error ocurred during the send operation.
        :type error: ~Exception
        :rtype: None
        """
        event = {
            "message_id": self._request_id,
            "result": result,
            "error": str(error)
        }
        _record_event("MessageSendComplete", event)
        return super(Message, self)._on_message_sent(result, error=error)

    def gather(self):
        """Return all the messages represented by this object.
        This will always be a list of a single message.
        :returns: list[~uamqp.Message]
        """
        return super(Message, self).gather()

    def get_message(self):
        """Get the underlying C message from this object.
        :returns: ~uamqp.c_uamqp.cMessage
        """
        _record_event("MessageSendPending", {"message_id": self._request_id})
        return super(Message, self).get_message()


class Connection(uamqp.connection.Connection):
    """An AMQP Connection. A single Connection can have multiple Sessions, and
    can be shared between multiple Clients. This Connection supports recording and playback
    for test suites.

    :ivar max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :vartype max_frame_size: int
    :ivar channel_max: Maximum number of Session channels in the Connection.
    :vartype channel_max: int
    :ivar idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :vartype idle_timeout: int
    :ivar properties: Connection properties.
    :vartype properties: dict

    :param hostname: The hostname of the AMQP service with which to establish
     a connection.
    :type hostname: bytes or str
    :param sasl: Authentication for the connection. If none is provided SASL Annoymous
     authentication will be used.
    :type sasl: ~uamqp.authentication.AMQPAuth
    :param container_id: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type container_id: str or bytes
    :param max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :type max_frame_size: int
    :param channel_max: Maximum number of Session channels in the Connection.
    :type channel_max: int
    :param idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :type idle_timeout: int
    :param properties: Connection properties.
    :type properties: dict
    :param remote_idle_timeout_empty_frame_send_ratio: Ratio of empty frames to
     idle time for Connections with no activity. Value must be between
     0.0 and 1.0 inclusive. Default is 0.5.
    :type remote_idle_timeout_empty_frame_send_ratio: float
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 properties=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 debug=False,
                 encoding='UTF-8',
                 playback=False):
        self._line_offset = []
        self._recording = os.path.join(directory, filename)
        self._playback = playback
        if self._playback:
            offset = 0
            with open(self._recording, 'r') as recording_data:
                for line in recording_data:
                    self._line_offset.append(offset)
                    offset += len(line)

            self.container_id = container_id if container_id else str(uuid.uuid4())
            self.hostname = hostname
            self.auth = sasl
            self.cbs = None
            self._conn = None
            self._lock = threading.Lock()
            self._state = c_uamqp.ConnectionState.UNKNOWN
            self._encoding = encoding
            self._max_frame_size = max_frame_size
            self._channel_max = channel_max
            self._idle_timeout = idle_timeout
            self._properties = properties
            self._remote_idle_timeout_empty_frame_send_ratio = remote_idle_timeout_empty_frame_send_ratio
        else:
            super(Connection, self).__init__(hostname, sasl,
                container_id=container_id,
                max_frame_size=max_frame_size,
                channel_max=channel_max,
                idle_timeout=idle_timeout,
                properties=properties,
                remote_idle_timeout_empty_frame_send_ratio=remote_idle_timeout_empty_frame_send_ratio,
                debug=debug,
                encoding=encoding)

    def _state_changed(self, previous_state, new_state):
        """Callback called whenever the underlying Connection undergoes
        a change of state. This function wraps the states as Enums for logging
        purposes.
        :param previous_state: The previous Connection state.
        :type previous_state: int
        :param new_state: The new Connection state.
        :type new_state: int
        """
        event = {
            "connection_id": self.container_id,
            "previous_state": previous_state,
            "new_state": new_state
        }
        _record_event("ConnectionState", event)
        super(Connection, self)._state_changed(previous_state, new_state)

    def destroy(self):
        """Close the connection, and close any associated
        CBS authentication session.
        """
        if not self._playback:
            super(Connection, self).destroy()

    def work(self):
        """Perform a single Connection iteration."""
        if not self._playback:
            super(Connection, self).work()

    @property
    def max_frame_size(self):
        if self._playback:
            return self._max_frame_size
        else:
            return super(Connection, self).max_frame_size

    @max_frame_size.setter
    def max_frame_size(self, value):
        if self._playback:
            self._max_frame_size = int(value)
        else:
            self._conn.max_frame_size = int(value)

    @property
    def channel_max(self):
        if self._playback:
            return self._channel_max
        else:
            return super(Connection, self).channel_max

    @channel_max.setter
    def channel_max(self, value):
        if self._playback:
            self._channel_max = int(value)
        else:
            self._conn.channel_max = int(value)

    @property
    def idle_timeout(self):
        if self._playback:
            return self._idle_timeout
        else:
            return super(Connection, self).idle_timeout

    @idle_timeout.setter
    def idle_timeout(self, value):
        if self._playback:
            self._idle_timeout = int(value)
        else:
            self._conn.idle_timeout = int(value)

    @property
    def properties(self):
        if self._playback:
            return self._properties
        else:
            return super(Connection, self).properties

    @properties.setter
    def properties(self, value):
        if self._playback:
            self._properties = value
        else:
            self._conn.properties = utils.data_factory(value, encoding=self._encoding)

    @property
    def remote_max_frame_size(self):
        if self._playback:
            return self._max_frame_size
        else:
            return super(Connection, self).remote_max_frame_size


class MessageSender(uamqp.sender.MessageSender):
    """A Message Sender that opens its own exclsuive Link on an
    existing Session. This message sender supports recording and playback
    for test suites.

    :ivar send_settle_mode: The mode by which to settle message send
     operations. If set to `Unsettled`, the client will wait for a confirmation
     from the service that the message was successfully send. If set to 'Settled',
     the client will not wait for confirmation and assume success.
    :vartype send_settle_mode: ~uamqp.constants.SenderSettleMode
    :ivar max_message_size: The maximum allowed message size negotiated for the Link.
    :vartype max_message_size: int

    :param session: The underlying Session with which to send.
    :type session: ~uamqp.Session
    :param source: The name of source (i.e. the client).
    :type source: str or bytes
    :param target: The AMQP endpoint to send to.
    :type target: ~uamqp.Target
    :param name: A unique name for the sender. If not specified a GUID will be used.
    :type name: str or bytes
    :param send_settle_mode: The mode by which to settle message send
     operations. If set to `Unsettled`, the client will wait for a confirmation
     from the service that the message was successfully send. If set to 'Settled',
     the client will not wait for confirmation and assume success.
    :type send_settle_mode: ~uamqp.constants.SenderSettleMode
    :param max_message_size: The maximum allowed message size negotiated for the Link.
    :type max_message_size: int
    :param link_credit: The sender Link credit that determines how many
     messages the Link will attempt to handle per connection iteration.
    :type link_credit: int
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
                 name=None,
                 send_settle_mode=None,
                 max_message_size=None,
                 link_credit=None,
                 properties=None,
                 debug=False,
                 encoding='UTF-8',
                 playback=False):
        self._sender_id = str(uuid.uuid4())
        self._playback = playback
        if self._playback:
            if name:
                self.name = name.encode(encoding) if isinstance(name, str) else name
            else:
                self.name = str(uuid.uuid4()).encode(encoding)
            source = source.encode(encoding) if isinstance(source, str) else source
            role = constants.Role.Sender

            self.source = c_uamqp.Messaging.create_source(source)
            self.target = target._address.value
            self._conn = session._conn
            self._session = session
            self._link = None
            self._link_credit = link_credit
            self._properties = properties
            self._send_settle_mode = send_settle_mode
            self._max_message_size = max_message_size
            self._sender = None
            self._state = constants.MessageSenderState.Idle
        else:
            super(MessageSender, self).__init__(
                session, source, target,
                name=name,
                send_settle_mode=send_settle_mode,
                max_message_size=max_message_size,
                link_credit=link_credit,
                properties=properties,
                debug=debug,
                encoding=encoding)

    def destroy(self):
        """Close both the Sender and the Link. Clean up any C objects."""
        if not self._playback:
            super(MessageSender, self).destroy()

    def open(self):
        """Open the MessageSender in order to start processing messages.

        :raises: ~uamqp.errors.AMQPConnectionError if the Sender raises
         an error on opening. This can happen if the target URI is invalid
         or the credentials are rejected.
        """
        if not self._playback:
            super(MessageSender, self).open()

    def send_async(self, message, timeout=0):
        """Add a single message to the internal pending queue to be processed
        by the Connection without waiting for it to be sent.
        :param message: The message to send.
        :type message: ~uamqp.Message
        :param timeout: An expiry time for the message added to the queue. If the
         message is not sent within this timeout it will be discarded with an error
         state. If set to 0, the message will not expire. The default is 0.
        """
        if not self._playback:
            super(MessageSender, self).send_async(message, timeout=timeout)

    def _state_changed(self, previous_state, new_state):
        """Callback called whenever the underlying Sender undergoes a change
        of state. This function wraps the states as Enums to prepare for
        calling the public callback.
        :param previous_state: The previous Sender state.
        :type previous_state: int
        :param new_state: The new Sender state.
        :type new_state: int
        """
        event = {
            "sender_id": self._sender_id,
            "previous_state": previous_state,
            "new_state": new_state
        }
        _record_event("MessageSenderState", event)
        super(MessageSender, self)._state_changed(previous_state, new_state)

    @property
    def send_settle_mode(self):
        if self._playback:
            return self._send_settle_mode
        else:
            return super(MessageSender, self).properties

    @send_settle_mode.setter
    def send_settle_mode(self, value):
        if self._playback:
            self._send_settle_mode = value.value
        else:
            self._link.send_settle_mode = value.value

    @property
    def max_message_size(self):
        if self._playback:
            return self._max_message_size
        else:
            return super(MessageSender, self).max_message_size

    @max_message_size.setter
    def max_message_size(self, value):
        if self._playback:
            self._max_message_size = int(value)
        else:
            self._link.max_message_size = int(value)

