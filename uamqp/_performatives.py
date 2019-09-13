#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from ._encode import encode_value
from ._decode import decode_value
from ._error import AMQPError
from .types import TYPE, VALUE, AMQPTypes


def get_frame(frame_type, data, offset):
    values = decode_value(data)
    descriptor = values[VALUE][0][VALUE]

    if descriptor == CloseFrame.header:
        return CloseFrame.from_response(values[VALUE][1][VALUE])
    elif descriptor == OpenFrame.header:
        return OpenFrame.from_response(values[VALUE][1][VALUE])


class OpenFrame(object):
    """
    <type name="open" class="composite" source="list" provides="frame">
        <descriptor name="amqp:open:list" code="0x00000000:0x00000010"/>
        <field name="container-id" type="string" mandatory="true"/>
        <field name="hostname" type="string"/>
        <field name="max-frame-size" type="uint" default="4294967295"/>
        <field name="channel-max" type="ushort" default="65535"/>
        <field name="idle-time-out" type="milliseconds"/>
        <field name="outgoing-locales" type="ietf-language-tag" multiple="true"/>
        <field name="incoming-locales" type="ietf-language-tag" multiple="true"/>
        <field name="offered-capabilities" type="symbol" multiple="true"/>
        <field name="desired-capabilities" type="symbol" multiple="true"/>
        <field name="properties" type="fields"/>
    </type>
    """

    header = 16

    def __init__(
        self,
        container_id,
        hostname=None,
        max_frame_size=None,
        channel_max=None,
        idle_time_out=None,
        outgoing_locales=None,
        incoming_locales=None,
        offered_capabilities=None,
        desired_capabilities=None,
        properties=None,
    ):
        self.container_id = container_id
        self.hostname = hostname
        self.max_frame_size = max_frame_size
        self.channel_max = channel_max
        self.idle_time_out = idle_time_out
        self.outgoing_locales = outgoing_locales
        self.incoming_locales = incoming_locales
        self.offered_capabilities = offered_capabilities
        self.desired_capabilities = desired_capabilities
        self.properties = properties

    @classmethod
    def from_response(cls, data):
        return cls(
            container_id=data[0][VALUE],
            hostname=data[1][VALUE],
            max_frame_size=data[2][VALUE],
            channel_max=data[3][VALUE],
            idle_time_out=data[4][VALUE],
            outgoing_locales=data[5][VALUE],
            incoming_locales=data[6][VALUE],
            offered_capabilities=data[7][VALUE],
            desired_capabilities=data[8][VALUE],
            properties=data[9][VALUE])     

    def encode(self):
        body = [{TYPE: AMQPTypes.string, VALUE: self.container_id}]
        if self.hostname:
            body.append({TYPE: AMQPTypes.string, VALUE: self.hostname})
        if self.max_frame_size:
            body.append({TYPE: AMQPTypes.uint, VALUE: self.max_frame_size})
        if self.channel_max:
            body.append({TYPE: AMQPTypes.ushort, VALUE: self.channel_max})

        frame = {
            TYPE: AMQPTypes.described,
            VALUE: (
                {TYPE: AMQPTypes.ulong, VALUE: self.header},
                {TYPE: AMQPTypes.list, VALUE: body}
            )
        }
        offset = b"\x02"
        type_code = b"\x00"
        frame_data = encode_value(b"", frame)
        size = len(frame_data).to_bytes(4, 'big')
        header = size + offset + type_code
        return frame_data, header

    def log(self):
        return "OpenFrame"


class CloseFrame(object):
    """
    <type name="close" class="composite" source="list" provides="frame">
        <descriptor name="amqp:close:list" code="0x00000000:0x00000018"/>
        <field name="error" type="error"/>
    </type>
    """

    header = 24

    def __init__(self, error=None):
        self.error = error

    @classmethod
    def from_response(cls, data):
        error = None
        if data:
            error_field = data[0]
            if error_field[0][VALUE] != AMQPError.header:
                raise ValueError("Received invalid CLOSE response.")
            error = AMQPError.from_response(error_field[1][VALUE])
        return cls(error=error)
