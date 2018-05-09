#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import uuid
import json

import uamqp

def _record_event(event_type, data):
    directory = "C:\\Users\\antisch\\Documents\\GitHub\\azure-uamqp-python\\samples\\recordings"
    filename = "test_recording.txt"
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
        _record_event("MessageSendComplete", {"request_id": self._request_id})
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
        _record_event("MessageSendPending", {"request_id": self._request_id})
        return super(Message, self).get_message()


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

    def __init__(self, *args, **kwargs):
        self._sender_id = str(uuid.uuid4())
        super(MessageSender, self).__init__(*args, **kwargs)

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

