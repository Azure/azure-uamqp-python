#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from io import BytesIO
from collections import namedtuple

from ._encode import encode_value
from ._decode import decode_value
from .definitions import _FIELD_DEFINITIONS
from .types import TYPE, VALUE, AMQPTypes, FieldDefinition


FIELD = namedtuple('field', 'name, type, mandatory, default, multiple')


class Performative(object):

    NAME = None
    CODE = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return "{{{} [{}]}}".format(self.NAME, self.__dict__)


class OpenFrame(Performative):
    """OPEN performative. Negotiate Connection parameters.

    The first frame sent on a connection in either direction MUST contain an Open body.
    (Note that theConnection header which is sent first on the Connection is *not* a frame.)
    The fields indicate thecapabilities and limitations of the sending peer.

    :param str container_id: The ID of the source container.
    :param str hostname: The name of the target host.
        The dns name of the host (either fully qualified or relative) to which the sendingpeer is connecting.
        It is not mandatory to provide the hostname. If no hostname isprovided the receiving peer should select
        a default based on its own configuration.This field can be used by AMQP proxies to determine the correct
        back-end service toconnect the client to.This field may already have been specified by the sasl-init frame,
        if a SASL layer is used, or, the server name indication extension as described in RFC-4366, if a TLSlayer
        is used, in which case this field SHOULD be null or contain the same value. It is undefined what a different
        value to those already specific means.
    """
    NAME = "OPEN"
    CODE = 16
    DEFINITION = {
        FIELD("container_id", AMQPTypes.string, True, None, False),
        FIELD("hostname", AMQPTypes.string, False, None, False),
        FIELD("max_frame_size", AMQPTypes.uint, False, None, 4294967295),
        FIELD("channel_max", AMQPTypes.ushort, False, None, 65535),
        FIELD("idle_time_out", FieldDefinition.milliseconds, False, None, False),
        FIELD("outgoing_locales", FieldDefinition.ietf_language_tag, False, None, True),
        FIELD("incoming_locales", FieldDefinition.ietf_language_tag, False, None, True),
        FIELD("offered_capabilities", AMQPTypes.symbol, False, None, True),
        FIELD("desired_capabilities", AMQPTypes.symbol, False, None, True),
        FIELD("properties", FieldDefinition.fields, False, None, False),
    }


class CloseFrame(Performative):
    """
    <type name="close" class="composite" source="list" provides="frame">
        <descriptor name="amqp:close:list" code="0x00000000:0x00000018"/>
        <field name="error" type="error"/>
    </type>
    """
    NAME = "CLOSE"
    CODE = 24
    DEFINITION = {FIELD("error", FieldDefinition.error, False, None, False)}


PERFORMATIVES = {
    16: OpenFrame,
    24: CloseFrame,
}


def decode_frame(data, offset):
    # type: (type, bytes) -> Performative
    _ = data[:offset]  # TODO: Extra data
    buffer = BytesIO(data[offset:])
    descriptor, fields = decode_value(buffer)
    frame_type = PERFORMATIVES[descriptor]

    kwargs = {}
    for index, field in enumerate(frame_type.DEFINITION):
        value = fields[index]
        if value is None and field.default:
            value = field.default
        if field.type is FieldDefinition:
            kwargs[field.name] = _FIELD_DEFINITIONS[field.type].decode(value)
        else:
            kwargs[field.name] = value
    return frame_type(**kwargs)


def encode_frame(frame):
    # type: (Performative) -> Tuple(bytes, bytes)
    body = []
    for field in frame.DEFINITION:
        value = frame.__dict__[field.name]
        if value is None and field.mandatory:
            raise ValueError("Performative missing mandatory field {}".format(field.name))
        if field.type is FieldDefinition:
            body.append(_FIELD_DEFINITIONS[field.type].encode(value))
        else:
            body.append({TYPE: field.type, VALUE: value})

        frame = {
            TYPE: AMQPTypes.described,
            VALUE: (
                {TYPE: AMQPTypes.ulong, VALUE: frame.CODE},
                {TYPE: AMQPTypes.list, VALUE: body}
            )
        }
        offset = b"\x02"
        type_code = b"\x00"
        frame_data = encode_value(b"", frame)
        size = len(frame_data).to_bytes(4, 'big')
        header = size + offset + type_code
        return frame_data, header
