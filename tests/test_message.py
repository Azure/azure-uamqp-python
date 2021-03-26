import pytest

from uamqp.message import MessageProperties, Message, SequenceBody, DataBody, ValueBody
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
