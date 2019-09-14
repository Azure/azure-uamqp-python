#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from datetime import timedelta
from enum import Enum

import six

from .types import TYPE, VALUE, AMQPTypes, FieldDefinition
from .error import (
    AMQPError,
    ErrorCondition,
    AMQPConnectionError,
    AMQPConnectionRedirect,
    ConnectionErrorCondition,
    AMQPSessionError,
    SessionErrorCondition,
    AMQPLinkError,
    AMQPLinkRedirect,
    LinkErrorCondition)


_FIELD_DEFINITIONS = {
    FieldDefinition.role: RoleField,
    FieldDefinition.sender_settle_mode: SenderSettleModeField,
    FieldDefinition.receiver_settle_mode: ReceiverSettleModeField,
    FieldDefinition.handle: HandleField,
    FieldDefinition.seconds: SecondsField,
    FieldDefinition.milliseconds: MillisecondsField,
    FieldDefinition.delivery_tag: DeliveryTagField,
    FieldDefinition.delivery_number: DeliveryNumberField,
    FieldDefinition.transfer_number: TransferNumberField,
    FieldDefinition.sequence_no: SequenceNoField,
    FieldDefinition.message_format: MessageFormatField,,
    FieldDefinition.ietf_language_tag: IETFLanguageTagField,
    FieldDefinition.fields: FieldsField,
    FieldDefinition.error: ErrorField,
}


class RoleField(object):
    """Link endpoint role.
    
    Valid Values:
        - False/"SENDER": Sender
        - True/"RECEIVER": Receiver

    <type name="role" class="restricted" source="boolean">
        <choice name="sender" value="false"/>
        <choice name="receiver" value="true"/>
    </type>
    """

    @staticmethod
    def encode(value):
        # type: (Union[bool, str]) -> Dict[str, Any]
        if value == 'SENDER':
            return {TYPE: AMQPTypes.boolean, VALUE: False}
        if value == 'RECEIVER':
            return {TYPE: AMQPTypes.boolean, VALUE: True}
        if value not in [True, False]:
            raise TypeError("Invalide Role value: {}".format(value))
        return {TYPE: AMQPTypes.boolean, VALUE: bool(value)}

    @staticmethod
    def decode(value):
        # type: (bool) -> str
        if value not in [True, False]:
            raise TypeError("Invalide Role value: {}".format(value))
        if value:
            return 'RECEIVER'
        return 'SENDER'


class SenderSettleModeField(object):
    """Settlement policy for a Sender.

    Valid Values:
        - 0/"UNSETTLED": The Sender will send all deliveries initially unsettled to the Receiver.
        - 1/"SETTLED": The Sender will send all deliveries settled to the Receiver.
        - 2/"MIXED": The Sender may send a mixture of settled and unsettled deliveries to the Receiver.
    
    <type name="sender-settle-mode" class="restricted" source="ubyte">
        <choice name="unsettled" value="0"/>
        <choice name="settled" value="1"/>
        <choice name="mixed" value="2"/>
    </type>
    """
    @staticmethod
    def encode(value):
        # type: (Union[int, str]) -> Dict[str, Any]
        if value == 'UNSETTLED':
            return {TYPE: AMQPTypes.ubyte, VALUE: 0}
        if value == 'SETTLED':
            return {TYPE: AMQPTypes.ubyte, VALUE: 1}
        if value == 'MIXED':
            return {TYPE: AMQPTypes.ubyte, VALUE: 2}
        if value not in [0, 1, 2]:
            raise ValueError("Invalid SenderSettleMode: {}".format(value))
        return {TYPE: AMQPTypes.ubyte, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (int) -> str
        if value not in [0, 1, 2]:
            raise ValueError("Invalid SenderSettleMode: {}".format(value))
        if value == 0:
            return 'UNSETTLED'
        if value == 1:
            return 'SETTLED'
        return 'MIXED'


class ReceiverSettleModeField(object):
    """Settlement policy for a Receiver.

    Valid Values:
        - 0/"FIRST": The Receiver will spontaneously settle all incoming transfers.
        - 1/"SECOND": The Receiver will only settle after sending the disposition to the Sender and
          receiving a disposition indicating settlement of the delivery from the sender.
    
    <type name="receiver-settle-mode" class="restricted" source="ubyte">
        <choice name="first" value="0"/>
        <choice name="second" value="1"/>
    </type>
    """

    @staticmethod
    def encode(value):
        # type: (Union[int, str]) -> Dict[str, Any]

        if value == 'FIRST':
            return {TYPE: AMQPTypes.ubyte, VALUE: 0}
        if value == 'SECOND':
            return {TYPE: AMQPTypes.ubyte, VALUE: 1}
        if value not in [0, 1]:
            raise ValueError("Invalid ReceiverSettleMode: {}".format(value))
        return {TYPE: AMQPTypes.ubyte, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (int) -> str
        if value not in [0, 1]:
            raise ValueError("Invalid ReceiverSettleMode: {}".format(value))
        if value == 0:
            return 'FIRST'
        return 'SECOND'


class HandleField(object):
    """The handle of a Link.

    An alias established by the attach frame and subsequently used by endpoints as a shorthand to refer
    to the Link in all outgoing frames. The two endpoints may potentially use different handles to refer
    to the same Link. Link handles may be reused once a Link is closed for both send and receive.
    
    <type name="handle" class="restricted" source="uint"/>
    """

    @staticmethod
    def encode(value):
        # type: (int) -> Dict[str, Any]
        if value is None:
            raise TypeError("Invalid NULL Handle")
        return {TYPE: AMQPTypes.uint, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (int) -> int
        if value is None:
            raise TypeError("Invalid NULL Handle")
        return value


class SecondsField(object):
    """A duration measured in seconds.
    
    <type name="seconds" class="restricted" source="uint"/>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[timedelta]) -> Dict[str, Any]
        if value is None:
            return {TYPE: AMQPTypes.null, VALUE: None}
        return {TYPE: AMQPTypes.uint, VALUE: value.seconds}

    @staticmethod
    def decode(value):
        # type: (Optional[int]) -> Optional[timedelta]
        if value is None:
            return None
        return timedelta(seconds=value)



class MillisecondsField(object):
    """A duration measured in milliseconds.

    <type name="milliseconds" class="restricted" source="uint"/>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[timedelta]) -> Dict[str, Any]
        if value is None:
            return {TYPE: AMQPTypes.null, VALUE: None}
        milliseconds = int(value.microseconds/1000.0)
        return {TYPE: AMQPTypes.uint, VALUE: milliseconds}

    @staticmethod
    def decode(value):
        # type: (Optional[int]) -> Optional[timedelta]
        if value is None:
            return None
        return timedelta(milliseconds=value)


class DeliveryTagField(object):
    """A delivery-tag may be up to 32 octets of binary data.
    
    <type name="delivery-tag" class="restricted" source="binary"/>
    """
    
    @staticmethod
    def encode(value):
        # type: (bytes) -> Dict[str, Any]
        if value is None:
            raise TypeError("Invalid NULL delivery tag")
        if not isinstance(value, six.binary_type):
            raise TypeError("Delivery tag must be bytes")
        return {TYPE: AMQPTypes.binary, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (bytes) -> bytes
        if value is None:
            raise TypeError("Invalid NULL delivery tag")
        return value


class SequenceNoField(object):
    """32-bit RFC-1982 serial number.

    A sequence-no encodes a serial number as defined in RFC-1982.
    The arithmetic, and operators forthese numbers are defined by RFC-1982.
    
    <type name="sequence-no" class="restricted" source="uint"/>
    """

    @staticmethod
    def encode(value):
        # type: (int) -> Dict[str, Any]
        if value is None:
            raise TypeError("Invalid NULL sequence no")
        return {TYPE: AMQPTypes.uint, VALUE: int(value)}

    @staticmethod
    def decode(value):
        # type: (int) -> int
        if value is None:
            raise TypeError("Invalid NULL sequence no.")
        return value


class DeliveryNumberField(SequenceNoField):
    """32-bit RFC-1982 serial number.

    A Deliver number encodes a serial number as defined in RFC-1982.
    The arithmetic, and operators forthese numbers are defined by RFC-1982.
    
    <type name="delivery-number" class="restricted" source="sequence-no"/>
    """


class TransferNumberField(SequenceNoField):
    """32-bit RFC-1982 serial number.

    A Transfer number encodes a serial number as defined in RFC-1982.
    The arithmetic, and operators forthese numbers are defined by RFC-1982.
    
    <type name="transfer-number" class="restricted" source="sequence-no"/>
    """


class MessageFormatField(object):
    """32-bit message format code.

    The upper three octets of a message format code identify a particular message format. The lowest
    octet indicates the version of said message format. Any given version of a format is forwards compatible
    with all higher versions.

            3 octets      1 octet
        +----------------+---------+
        | message format | version |
        +----------------+---------+
        |                          |
        msb                        lsb
    
    <type name="message-format" class="restricted" source="uint"/>
    """

    @staticmethod
    def encode(value):
        # type: (int) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.uint, VALUE: 0}
        return {TYPE: AMQPTypes.uint, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (Optional[int]) -> int
        if not value:
            return 0
        return value


class IETFLanguageTagField(object):
    """An IETF language tag as defined by BCP 47.

    IETF language tags are abbreviated language codes as defined in the IETF Best Current PracticeBCP-47
    (http://www.rfc-editor.org/rfc/bcp/bcp47.txt) (incorporating  RFC-5646
    (http://www.rfc-editor.org/rfc/rfc5646.txt)). A list of registered subtags is maintained in the IANA
    Language SubtagRegistry (http://www.iana.org/assignments/language-subtag-registry). All AMQP implementations
    should understand at the least the IETF language tagen-US(note thatthis uses a hyphen separator, not an
    underscore).
    
    <type name="ietf-language-tag" class="restricted" source="symbol"/>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[str]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        tag = ",".join(value).encode('utf-8')
        return {TYPE: AMQPTypes.symbol, VALUE: tag}

    @staticmethod
    def decode(value):
        # type: (Optional[str]) -> List[str]
        if value:
            return value.decode('utf-8').split(',')
        return []


class FieldsField(object):
    """A mapping from field name to value.
    
    The fields type is a map where the keys are restricted to be of type symbol (this excludes the possibility
    of a null key).  There is no further restriction implied by the fields type on the allowed values for the
    entries or the set of allowed keys.

    <type name="fields" class="restricted" source="map"/>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        fields = {TYPE: AMQPTypes.map, VALUE:[]}
        for key, data in value.items():
            if isinstance(key, six.text_type):
                key = key.encode('utf-8')
            fields[VALUE].append(({TYPE: AMQPTypes.symbol, VALUE: key}, value))
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        return value or {}


class ErrorField(object):
    """Details of an error.

    <type name="error" class="composite" source="list">
        <descriptor name="amqp:error:list" code="0x00000000:0x0000001d"/>
        <field name="condition" type="symbol" requires="error-condition" mandatory="true"/>
        <field name="description" type="string"/>
        <field name="info" type="fields"/>
    </type>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[AMQPError]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        value = ({TYPE: AMQPTypes.ulong, VALUE: 29}, [])
        try:
            value[1].append({TYPE: AMQPTypes.symbol, VALUE: value.condition.value})
        except AttributeError:
            value[1].append({TYPE: AMQPTypes.symbol, VALUE: value.condition})
        value[1].append(value.description or None)
        value[1].append(encode_fields(value.info))
        return value

    @staticmethod
    def decode(value):
        # type: (Optional[Tuple(int, List[Any])]) -> Optional[AMQPError]
        if value and value[0] == 29:
            condition = value[1][0]
            description = value[1][1].decode('utf-8') if len(value[1]) > 1 else None
            info = value[1][2] if len(value[1]) > 2 else {}
            try:
                if ":link:" in condition:
                    condition = LinkErrorCondition(condition)
                    if condition == LinkErrorCondition.Redirect:
                        return AMQPLinkRedirect(condition, description=description, info=info)
                    return AMQPLinkError(condition, description=description, info=info)
                if ":session:" in condition:
                    condition = SessionErrorCondition(condition)
                    return AMQPSessionError(condition, description=description, info=info)
                if ":connection:" in condition:
                    condition = ConnectionErrorCondition(condition)
                    if condition == ConnectionErrorCondition.Redirect:
                        return AMQPConnectionRedirect(condition, description=description, info=info)
                    return AMQPConnectionError(condition, description=description, info=info)
                condition = ErrorCondition(condition)
            except ValueError:
                pass
            return AMQPError(condition, description=description, info=info)
        return None
