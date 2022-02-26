#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
import copy
import pickle
import pytest

from uamqp.message import (
    MessageProperties,
    MessageHeader,
    Message,
    constants,
    errors,
    c_uamqp,
    SequenceBody,
    DataBody,
    ValueBody,
    BatchMessage
)
from uamqp import MessageBodyType


def test_message_properties():

    properties = MessageProperties()
    assert properties.user_id is None

    properties = MessageProperties()
    properties.user_id = b''
    assert properties.user_id == b''

    properties = MessageProperties()
    properties.user_id = '1'
    assert properties.user_id == b'1'

    properties = MessageProperties()
    properties.user_id = 'short'
    assert properties.user_id == b'short'

    properties = MessageProperties()
    properties.user_id = 'longuseridstring'
    assert properties.user_id == b'longuseridstring'

    properties = MessageProperties()
    properties.user_id = '!@#$%^&*()_+1234567890'
    assert properties.user_id == b'!@#$%^&*()_+1234567890'

    properties = MessageProperties()
    properties.user_id = 'werid/0\0\1\t\n'
    assert properties.user_id == b'werid/0\0\1\t\n'

def send_complete_callback(result, error):
    # helper for test below not in test, b/c results in:
    # AttributeError: Can't pickle local object
    print(result)
    print(error)


def test_message_pickle():
    properties = MessageProperties()
    properties.message_id = '2'
    properties.user_id = '1'
    properties.to = 'dkfj'
    properties.subject = 'dsljv'
    properties.reply_to = "kdjfk"
    properties.correlation_id = 'ienag'
    properties.content_type = 'b'
    properties.content_encoding = '39ru'
    properties.absolute_expiry_time = 24
    properties.creation_time = 10
    properties.group_id = '3irow'
    properties.group_sequence = 39
    properties.reply_to_group_id = '39rud'

    header = MessageHeader()
    header.delivery_count = 3
    header.time_to_live = 5
    header.first_acquirer = 'dkfj'
    header.durable = True
    header.priority = 4

    data_message = Message(body=[b'testmessage1', b'testmessage2'])
    pickled = pickle.loads(pickle.dumps(data_message))
    body = list(pickled.get_data())
    assert len(body) == 2
    assert body == [b'testmessage1', b'testmessage2']

    sequence_message = Message(
        body=[[1234.56, b'testmessage2', True], [-1234.56, {b'key': b'value'}, False]],
        body_type=MessageBodyType.Sequence
    )
    pickled = pickle.loads(pickle.dumps(sequence_message))
    body = list(pickled.get_data())
    assert len(body) == 2
    assert body == [[1234.56, b'testmessage2', True], [-1234.56, {b'key': b'value'}, False]]

    value_message = Message(
        body={b'key': [1, b'str', False]},
        body_type=MessageBodyType.Value
    )
    pickled = pickle.loads(pickle.dumps(value_message))
    body = pickled.get_data()
    assert body == {b'key': [1, b'str', False]}

    error = errors.MessageModified(False, False, {b'key': b'value'})
    pickled_error = pickle.loads(pickle.dumps(error))
    assert pickled_error._annotations == {b'key': b'value'} # pylint: disable=protected-access

    message = Message(body="test", properties=properties, header=header)
    message.on_send_complete = send_complete_callback
    message.footer = {'a':2}
    message.state = constants.MessageState.ReceivedSettled

    pickled = pickle.loads(pickle.dumps(message))
    assert list(message.get_data()) == [b"test"]
    assert message.footer == pickled.footer
    assert message.state == pickled.state
    assert message.application_properties == pickled.application_properties
    assert message.annotations == pickled.annotations
    assert message.delivery_annotations == pickled.delivery_annotations
    assert message.settled == pickled.settled
    assert message.properties.message_id == pickled.properties.message_id
    assert message.properties.user_id == pickled.properties.user_id
    assert message.properties.to == pickled.properties.to
    assert message.properties.subject == pickled.properties.subject
    assert message.properties.reply_to == pickled.properties.reply_to
    assert message.properties.correlation_id == pickled.properties.correlation_id
    assert message.properties.content_type == pickled.properties.content_type
    assert message.properties.content_encoding == pickled.properties.content_encoding
    assert message.properties.absolute_expiry_time == pickled.properties.absolute_expiry_time
    assert message.properties.creation_time == pickled.properties.creation_time
    assert message.properties.group_id == pickled.properties.group_id
    assert message.properties.group_sequence == pickled.properties.group_sequence
    assert message.properties.reply_to_group_id == pickled.properties.reply_to_group_id
    assert message.header.delivery_count == pickled.header.delivery_count
    assert message.header.time_to_live == pickled.header.time_to_live
    assert message.header.first_acquirer == pickled.header.first_acquirer
    assert message.header.durable == pickled.header.durable
    assert message.header.priority == pickled.header.priority

    # send with message param
    settler = errors.MessageAlreadySettled
    internal_message = c_uamqp.create_message()
    internal_message.add_body_data(b"hi")
    message_w_message_param = Message(
        message=internal_message,
        settler=settler,
        delivery_no=1
    )
    pickled = pickle.loads(pickle.dumps(message_w_message_param))
    message_data = str(message_w_message_param.get_data())
    pickled_data = str(pickled.get_data())

    assert message_data == pickled_data
    assert message_w_message_param.footer == pickled.footer
    assert message_w_message_param.state == pickled.state
    assert message_w_message_param.application_properties == pickled.application_properties
    assert message_w_message_param.annotations == pickled.annotations
    assert message_w_message_param.delivery_annotations == pickled.delivery_annotations
    assert message_w_message_param.settled == pickled.settled
    assert pickled.delivery_no == 1
    assert type(pickled._settler()) == type(settler())  # pylint: disable=protected-access

def test_deepcopy_batch_message():
    ## DEEPCOPY WITH MESSAGES IN BATCH THAT HAVE HEADER/PROPERTIES
    properties = MessageProperties()
    properties.message_id = '2'
    properties.user_id = '1'
    properties.to = 'dkfj'
    properties.subject = 'dsljv'
    properties.reply_to = "kdjfk"
    properties.correlation_id = 'ienag'
    properties.content_type = 'b'
    properties.content_encoding = '39ru'
    properties.absolute_expiry_time = 24
    properties.creation_time = 10
    properties.group_id = '3irow'
    properties.group_sequence = 39
    properties.reply_to_group_id = '39rud'

    header = MessageHeader()
    header.delivery_count = 3
    header.time_to_live = 5
    header.first_acquirer = 'dkfj'
    header.durable = True
    header.priority = 4

    message = Message(body="test", properties=properties, header=header)
    message.on_send_complete = send_complete_callback
    message.footer = {'a':2}
    message.state = constants.MessageState.ReceivedSettled

    message_batch = BatchMessage(
            data=[], multi_messages=False, properties=None
    )
    message_batch._body_gen.append(message)
    message_batch_copy = copy.deepcopy(message_batch)
    batch_message = list(message_batch._body_gen)[0]
    batch_copy_message = list(message_batch_copy._body_gen)[0]
    assert len(list(message_batch._body_gen)) == len(list(message_batch_copy._body_gen))

    # check message attributes are equal to deepcopied message attributes
    assert list(batch_message.get_data()) == list(batch_copy_message.get_data())
    assert batch_message.footer == batch_copy_message.footer
    assert batch_message.state == batch_copy_message.state
    assert batch_message.application_properties == batch_copy_message.application_properties
    assert batch_message.annotations == batch_copy_message.annotations
    assert batch_message.delivery_annotations == batch_copy_message.delivery_annotations
    assert batch_message.settled == batch_copy_message.settled
    assert batch_message.properties.message_id == batch_copy_message.properties.message_id
    assert batch_message.properties.user_id == batch_copy_message.properties.user_id
    assert batch_message.properties.to == batch_copy_message.properties.to
    assert batch_message.properties.subject == batch_copy_message.properties.subject
    assert batch_message.properties.reply_to == batch_copy_message.properties.reply_to
    assert batch_message.properties.correlation_id == batch_copy_message.properties.correlation_id
    assert batch_message.properties.content_type == batch_copy_message.properties.content_type
    assert batch_message.properties.content_encoding == batch_copy_message.properties.content_encoding
    assert batch_message.properties.absolute_expiry_time == batch_copy_message.properties.absolute_expiry_time
    assert batch_message.properties.creation_time == batch_copy_message.properties.creation_time
    assert batch_message.properties.group_id == batch_copy_message.properties.group_id
    assert batch_message.properties.group_sequence == batch_copy_message.properties.group_sequence
    assert batch_message.properties.reply_to_group_id == batch_copy_message.properties.reply_to_group_id
    assert batch_message.header.delivery_count == batch_copy_message.header.delivery_count
    assert batch_message.header.time_to_live == batch_copy_message.header.time_to_live
    assert batch_message.header.first_acquirer == batch_copy_message.header.first_acquirer
    assert batch_message.header.durable == batch_copy_message.header.durable
    assert batch_message.header.priority == batch_copy_message.header.priority

def test_message_auto_body_type():
    single_data = b'!@#$%^&*()_+1234567890'
    single_data_message = Message(body=single_data)
    check_list = [data for data in single_data_message.get_data()]
    assert isinstance(single_data_message._body, DataBody)
    assert len(check_list) == 1
    assert check_list[0] == single_data
    assert(str(single_data_message))

    multiple_data = [b'!@#$%^&*()_+1234567890', 'abcdefg~123']
    multiple_data_message = Message(body=multiple_data)
    check_list = [data for data in multiple_data_message.get_data()]
    assert isinstance(multiple_data_message._body, DataBody)
    assert len(check_list) == 2
    assert check_list[0] == multiple_data[0]
    assert check_list[1] == multiple_data[1].encode("UTF-8")
    assert (str(multiple_data_message))

    list_mixed_body = [b'!@#$%^&*()_+1234567890', 'abcdefg~123', False, 1.23]
    list_mixed_body_message = Message(body=list_mixed_body)
    check_data = list_mixed_body_message.get_data()
    assert isinstance(list_mixed_body_message._body, ValueBody)
    assert isinstance(check_data, list)
    assert len(check_data) == 4
    assert check_data[0] == list_mixed_body[0]
    assert check_data[1] == list_mixed_body[1].encode("UTF-8")
    assert check_data[2] == list_mixed_body[2]
    assert check_data[3] == list_mixed_body[3]
    assert (str(list_mixed_body_message))

    dic_mixed_body = {b'key1': b'value', b'key2': False, b'key3': -1.23}
    dic_mixed_body_message = Message(body=dic_mixed_body)
    check_data = dic_mixed_body_message.get_data()
    assert isinstance(dic_mixed_body_message._body, ValueBody)
    assert isinstance(check_data, dict)
    assert len(check_data) == 3
    assert check_data == dic_mixed_body
    assert (str(dic_mixed_body_message))


def test_message_body_data_type():
    single_data = b'!@#$%^&*()_+1234567890'
    single_data_message = Message(body=single_data, body_type=MessageBodyType.Data)
    check_list = [data for data in single_data_message.get_data()]
    assert isinstance(single_data_message._body, DataBody)
    assert len(check_list) == 1
    assert check_list[0] == single_data
    assert str(single_data_message)

    multiple_data = [b'!@#$%^&*()_+1234567890', 'abcdefg~123',]
    multiple_data_message = Message(body=multiple_data, body_type=MessageBodyType.Data)
    check_list = [data for data in multiple_data_message.get_data()]
    assert isinstance(multiple_data_message._body, DataBody)
    assert len(check_list) == 2
    assert check_list[0] == multiple_data[0]
    assert check_list[1] == multiple_data[1].encode("UTF-8")
    assert str(multiple_data_message)

    with pytest.raises(TypeError):
        Message(body={"key": "value"}, body_type=MessageBodyType.Data)

    with pytest.raises(TypeError):
        Message(body=1, body_type=MessageBodyType.Data)

    with pytest.raises(TypeError):
        Message(body=['abc', True], body_type=MessageBodyType.Data)

    with pytest.raises(TypeError):
        Message(body=True, body_type=MessageBodyType.Data)


def test_message_body_value_type():
    string_value = b'!@#$%^&*()_+1234567890'
    string_value_message = Message(body=string_value, body_type=MessageBodyType.Value)
    assert string_value_message.get_data() == string_value
    assert isinstance(string_value_message._body, ValueBody)
    assert str(string_value_message)

    float_value = 1.23
    float_value_message = Message(body=float_value, body_type=MessageBodyType.Value)
    assert float_value_message.get_data() == float_value
    assert isinstance(string_value_message._body, ValueBody)
    assert str(float_value_message)

    dict_value = {b"key1 ": b"value1", b'key2': -1, b'key3': False}
    dict_value_message = Message(body=dict_value, body_type=MessageBodyType.Value)
    assert dict_value_message.get_data() == dict_value
    assert isinstance(string_value_message._body, ValueBody)
    assert str(dict_value_message)

    compound_list_value = [1, b'abc', True, [1.23, b'abc', False], {b"key1 ": b"value1", b'key2': -1}]
    compound_list_value_message = Message(body=compound_list_value, body_type=MessageBodyType.Value)
    assert compound_list_value_message.get_data() == compound_list_value
    assert isinstance(string_value_message._body, ValueBody)
    assert str(compound_list_value_message)


def test_message_body_sequence_type():

    single_list = [1, 2, b'aa', b'bb', True, b"abc", {b"key1": b"value", b"key2": -1.23}]
    single_list_message = Message(body=single_list, body_type=MessageBodyType.Sequence)
    check_list = [data for data in single_list_message.get_data()]
    assert isinstance(single_list_message._body, SequenceBody)
    assert len(check_list) == 1
    assert check_list[0] == single_list
    assert str(single_list_message)

    multiple_lists = [[1, 2, 3, 4], [b'aa', b'bb', b'cc', b'dd']]
    multiple_lists_message = Message(body=multiple_lists, body_type=MessageBodyType.Sequence)
    check_list = [data for data in multiple_lists_message.get_data()]
    assert isinstance(multiple_lists_message._body, SequenceBody)
    assert len(check_list) == 2
    assert check_list[0] == multiple_lists[0]
    assert check_list[1] == multiple_lists[1]
    assert str(multiple_lists_message)

    with pytest.raises(TypeError):
        Message(body={"key": "value"}, body_type=MessageBodyType.Sequence)

    with pytest.raises(TypeError):
        Message(body=1, body_type=MessageBodyType.Sequence)

    with pytest.raises(TypeError):
        Message(body='a', body_type=MessageBodyType.Sequence)

    with pytest.raises(TypeError):
        Message(body=True, body_type=MessageBodyType.Sequence)
