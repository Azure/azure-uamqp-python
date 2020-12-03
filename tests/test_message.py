from uamqp.message import MessageProperties


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
