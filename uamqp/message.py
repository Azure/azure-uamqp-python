#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging

from uamqp import c_uamqp
from uamqp import utils
from uamqp import constants


_logger = logging.getLogger(__name__)


class Message:
    """An AMQP message. 
    
    When sending, depending on the nature of the data,
    different body encoding will be used. If the data is str or bytes, 
    a single part DataBody will be sent. If the data is a list or str/bytes,
    a multipart DataBody will be sent. Any other type of list will be sent
    as a SequenceBody, where as any other type of data will be sent as
    a ValueBody. An empty payload will also be sent as a ValueBody.

    :param body: The data to send in the message.
    :type body: Any Python data type.
    :param properties: Properties to add to the message.
    :type properties: ~uamqp.message.MessageProperties
    :param application_properties: Service specific application properties.
    :type application_properties: dict
    :param annotations: Service specific message annotations.
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

    def __init__(self,
                 body=None,
                 properties=None,
                 application_properties=None,
                 annotations=None,
                 msg_format=None,
                 message=None,
                 encoding='UTF-8'):
        self.state = constants.MessageState.WaitingToBeSent
        self.idle_time = 0
        self._retries = 0
        self._encoding = encoding
        self.on_send_complete = None
        self.properties = None
        self.application_properties = None
        self.annotations = None
        self.header = None
        self.footer = None
        self.delivery_annotations = None

        if message:
            self._parse_message(message)
        else:
            self._message = c_uamqp.create_message()
            if isinstance(body, (bytes, str)):
                self._body = DataBody(self._message)
                self._body.append(body)
            elif isinstance(body, list) and all([isinstance(b, (bytes,str)) for b in body]):
                self._body = DataBody(self._message)
                for value in body:
                    self._body.append(value)
            elif isinstance(body, list):
                self._body = SequenceBody(self._message)
                for value in body:
                    self._body.append(value)
            else:
                self._body = ValueBody(self._message)
                self._body.set(body)
            if msg_format:
                self._message.message_format = msg_format
            self.properties = properties
            self.application_properties = application_properties
            self.annotations = annotations

    def __str__(self):
        if not self._message:
            return ""
        return str(self._body)

    def _parse_message(self, message):
        self._message = message
        body_type = message.body_type
        if body_type == c_uamqp.MessageBodyType.NoneType:
            self._body = None
        elif body_type == c_uamqp.MessageBodyType.DataType:
            self._body = DataBody(self._message)
        elif body_type == c_uamqp.MessageBodyType.SequenceType:
            self._body = SequenceBody(self._message)
        else:
            self._body = ValueBody(self._message)
        _props = self._message.properties
        if _props:
            self.properties = MessageProperties(properties=_props, encoding=self._encoding)
        _header = self._message.header
        if _header:
            self.header = MessageHeader(header=_header)
        _footer = self._message.footer
        if _footer:
            self.footer = _footer.map
        _app_props = self._message.application_properties
        if _app_props:
            self.application_properties = _app_props.map
        _ann = self._message.message_annotations
        if _ann:
            self.annotations = _ann.map
        _delivery_ann = self._message.delivery_annotations
        if _delivery_ann:
            self.delivery_annotations = _delivery_ann.map

    def _on_message_sent(self, result, error=None):
        result = constants.MessageSendResult(result)
        if not error and result == constants.MessageSendResult.Error and self._retries < constants.MESSAGE_SEND_RETRIES:
            self._retries += 1
            _logger.debug("Message error, retrying. Attempts: {}".format(self._retries))
            self.state = constants.MessageState.WaitingToBeSent
        elif result == constants.MessageSendResult.Error:
            _logger.error("Message error, {} retries exhausted ({})".format(constants.MESSAGE_SEND_RETRIES, error))
            self.state = constants.MessageState.Failed
            if self.on_send_complete:
                self.on_send_complete(result, error)
        else:
            _logger.debug("Message sent: {}, {}".format(result, error))
            self.state = constants.MessageState.Complete
            if self.on_send_complete:
                self.on_send_complete(result, error)

    def get_message_encoded_size(self):
        # TODO: This no longer calculates the metadata accurately.
        return c_uamqp.get_encoded_message_size(self._message)

    def get_data(self):
        if not self._message:
            return None
        return self._body.data

    def gather(self):
        return [self]

    def get_message(self):
        if not self._message:
            return None
        if self.properties:
            self._message.properties = self.properties._properties  # pylint: disable=protected-access
        if self.application_properties:
            if not isinstance(self.application_properties, dict):
                raise TypeError("Application properties must be a dictionary.")
            amqp_props = utils.data_factory(self.application_properties, encoding=self._encoding)
            self._message.application_properties = amqp_props
        if self.annotations:
            if not isinstance(self.annotations, dict):
                raise TypeError("Message annotations must be a dictionary.")
            ann_props = c_uamqp.create_message_annotations(
                utils.data_factory(self.annotations, encoding=self._encoding))
            self._message.message_annotations = ann_props
        return self._message


class BatchMessage(Message):

    batch_format = 0x80013700
    max_message_length = constants.MAX_MESSAGE_LENGTH_BYTES
    _size_buffer = 65000

    def __init__(self,
                 data=None,
                 properties=None,
                 application_properties=None,
                 annotations=None,
                 multi_messages=False,
                 encoding='UTF-8'):  # pylint: disable=super-init-not-called
        self._multi_messages = multi_messages
        self._body_gen = data
        self._encoding = encoding
        self.on_send_complete = None
        self.properties = properties
        self.application_properties = application_properties
        self.annotations = annotations

    def _create_batch_message(self):
        return Message(body=[],
                       properties=self.properties,
                       annotations=self.annotations,
                       msg_format=self.batch_format,
                       encoding=self._encoding)

    def _multi_message_generator(self):
        while True:
            new_message = self._create_batch_message()
            message_size = new_message.get_message_encoded_size() + self._size_buffer
            body_size = 0
            try:
                for data in self._body_gen:
                    message_segment = []
                    if isinstance(data, str):
                        data = data.encode(self._encoding)
                    batch_data = c_uamqp.create_data(data)
                    c_uamqp.enocde_batch_value(batch_data, message_segment)
                    combined = b"".join(message_segment)
                    body_size += len(combined)
                    if (body_size + message_size) > self.max_message_length:
                        new_message.on_send_complete = self.on_send_complete
                        yield new_message
                        raise StopIteration()
                    else:
                        new_message._body.append(combined)  # pylint: disable=protected-access
            except StopIteration:
                _logger.debug("Sent partial message.")
                continue
            else:
                new_message.on_send_complete = self.on_send_complete
                yield new_message
                _logger.debug("Sent all batched data.")
                break

    def gather(self):
        if self._multi_messages:
            return self._multi_message_generator()

        new_message = self._create_batch_message()
        message_size = new_message.get_message_encoded_size() + self._size_buffer
        body_size = 0

        for data in self._body_gen:
            message_segment = []
            if isinstance(data, str):
                data = data.encode(self._encoding)
            batch_data = c_uamqp.create_data(data)
            c_uamqp.enocde_batch_value(batch_data, message_segment)
            combined = b"".join(message_segment)
            body_size += len(combined)
            if (body_size + message_size) > self.max_message_length:
                raise ValueError(
                    "Data set too large for a single message."
                    "Set multi_messages to True to split data across multiple messages.")
            new_message._body.append(combined)  # pylint: disable=protected-access
        new_message.on_send_complete = self.on_send_complete
        return [new_message]


class MessageProperties:

    def __init__(self,
                 message_id=None,
                 user_id=None,
                 to=None,
                 subject=None,
                 reply_to=None,
                 correlation_id=None,
                 content_type=None,
                 content_encoding=None,
                 absolute_expiry_time=None,
                 creation_time=None,
                 group_id=None,
                 group_sequence=None,
                 reply_to_group_id=None,
                 properties=None,
                 encoding='UTF-8'):
        self._properties = properties if properties else c_uamqp.cProperties()
        self._encoding = encoding
        if message_id:
            self.message_id = message_id
        if user_id:
            self.user_id = user_id
        if to:
            self.to = to
        if subject:
            self.subject = subject
        if reply_to:
            self.reply_to = reply_to
        if correlation_id:
            self.correlation_id = correlation_id
        if content_type:
            self.content_type = content_type
        if content_encoding:
            self.content_encoding = content_encoding
        if absolute_expiry_time:
            self.absolute_expiry_time = absolute_expiry_time
        if creation_time:
            self.creation_time = creation_time
        if group_id:
            self.group_id = group_id
        if group_sequence:
            self.group_sequence = group_sequence
        if reply_to_group_id:
            self.reply_to_group_id = reply_to_group_id

    @property
    def message_id(self):
        _value = self._properties.message_id
        if _value:
            return _value.value
        return None

    @message_id.setter
    def message_id(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.message_id = value

    @property
    def user_id(self):
        _value = self._properties.user_id
        if _value:
            return _value.value
        return None

    @user_id.setter
    def user_id(self, value):
        if isinstance(value, str):
            value = value.encode(self._encoding)
        elif not isinstance(value, bytes):
            raise TypeError("user_id must be bytes or str.")
        self._properties.user_id = value

    @property
    def to(self):
        _value = self._properties.to
        if _value:
            return _value.value
        return None

    @to.setter
    def to(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.to = value

    @property
    def subject(self):
        _value = self._properties.subject
        if _value:
            return _value.value
        return None

    @subject.setter
    def subject(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.subject = value

    @property
    def reply_to(self):
        _value = self._properties.reply_to
        if _value:
            return _value.value
        return None

    @reply_to.setter
    def reply_to(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.reply_to = value

    @property
    def correlation_id(self):
        _value = self._properties.correlation_id
        if _value:
            return _value.value
        return None

    @correlation_id.setter
    def correlation_id(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.correlation_id = value

    @property
    def content_type(self):
        _value = self._properties.content_type
        if _value:
            return _value.value
        return None

    @content_type.setter
    def content_type(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.content_type = value

    @property
    def content_encoding(self):
        _value = self._properties.content_encoding
        if _value:
            return _value.value
        return None

    @content_encoding.setter
    def content_encoding(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.content_encoding = value

    @property
    def absolute_expiry_time(self):
        _value = self._properties.absolute_expiry_time
        if _value:
            return _value.value
        return None

    @absolute_expiry_time.setter
    def absolute_expiry_time(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.absolute_expiry_time = value

    @property
    def creation_time(self):
        _value = self._properties.creation_time
        if _value:
            return _value.value
        return None

    @creation_time.setter
    def creation_time(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.creation_time = value

    @property
    def group_id(self):
        _value = self._properties.group_id
        if _value:
            return _value
        return None

    @group_id.setter
    def group_id(self, value):
        #value = utils.data_factory(value)
        self._properties.group_id = value

    @property
    def group_sequence(self):
        _value = self._properties.group_sequence
        if _value:
            return _value
        return None

    @group_sequence.setter
    def group_sequence(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.group_sequence = value

    @property
    def reply_to_group_id(self):
        _value = self._properties.reply_to_group_id
        if _value:
            return _value.value
        return None

    @reply_to_group_id.setter
    def reply_to_group_id(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._properties.reply_to_group_id = value


class MessageBody:

    def __init__(self, c_message, encoding='UTF-8'):
        self._message = c_message
        self._encoding = encoding

    def __str__(self):
        if self.type == c_uamqp.MessageBodyType.NoneType:
            return ""
        return str(self.data)

    @property
    def type(self):
        return self._message.body_type

    @property
    def data(self):
        raise NotImplementedError("Only MessageBody subclasses have data.")


class DataBody(MessageBody):

    def __str__(self):
        return "".join(self.data.decode(self._encoding))

    def __len__(self):
        return self._message.count_body_data()

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError("Index is out of range.")
        data = self._message.get_body_data(index)
        return data.value

    def append(self, other):
        if isinstance(other, str):
            self._message.add_body_data(other.encode(self._encoding))
        elif isinstance(other, bytes):
            self._message.add_body_data(other)

    @property
    def data(self):
        for i in range(len(self)):
            yield self._message.get_body_data(i)


class SequenceBody(MessageBody):

    def __len__(self):
        return self._message.count_body_sequence()

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError("Index is out of range.")
        data = self._message.get_body_sequence(index)
        return data.value

    def append(self, value):
        value = utils.data_factory(value, encoding=self._encoding)
        self._message.add_body_sequence(value)

    @property
    def data(self):
        for i in range(len(self)):  # pylint: disable=consider-using-enumerate
            yield self[i]


class ValueBody(MessageBody):

    def set(self, value):
        value = utils.data_factory(value)
        self._message.set_body_value(value)

    @property
    def data(self):
        _value = self._message.get_body_value()
        if _value:
            return _value.value
        return None


class MessageHeader:

    def __init__(self, header=None):
        self._header = header if header else c_uamqp.create_header()

    @property
    def delivery_count(self):
        return self._header.delivery_count

    @property
    def time_to_live(self):
        return self._header.time_to_live

    @property
    def durable(self):
        return self._header.durable

    @property
    def first_acquirer(self):
        return self._header.first_acquirer

    @property
    def priority(self):
        return self._header.priority
