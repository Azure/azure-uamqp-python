from uamqp.message import MessageProperties, MessageHeader, Message
import pickle


def test_message_proeprties():

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


    message = Message(properties=properties, header=header)
    message.footer = {'a':2}
    pickled = pickle.loads(pickle.dumps(message))

    assert message.footer == pickled.footer
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
