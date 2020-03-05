#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from datetime import timedelta
import struct
import uuid

import six

from .types import TYPE, VALUE, AMQPTypes, FieldDefinition, SASLCode
from .endpoints import TerminusDurability, ExpiryPolicy, DistributionMode
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
        # if value not in [0, 1, 2]:
        #     raise ValueError("Invalid SenderSettleMode: {}".format(value))
        # if value == 0:
        #     return 'UNSETTLED'
        # if value == 1:
        #     return 'SETTLED'
        # return 'MIXED'
        return value


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

        if value == 'FIRST':  # PeekLock
            return {TYPE: AMQPTypes.ubyte, VALUE: 0}
        if value == 'SECOND':  # ReceiveAndDelete
            return {TYPE: AMQPTypes.ubyte, VALUE: 1}
        if value not in [0, 1]:
            raise ValueError("Invalid ReceiverSettleMode: {}".format(value))
        return {TYPE: AMQPTypes.ubyte, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (int) -> str
        # if value not in [0, 1]:
        #     raise ValueError("Invalid ReceiverSettleMode: {}".format(value))
        # if value == 0:
        #     return 'FIRST'
        # return 'SECOND'
        return value


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
            {TYPE: AMQPTypes.null, VALUE: value}
        return {TYPE: AMQPTypes.uint, VALUE: value}

    @staticmethod
    def decode(value):
        # type: (Optional[int]) -> Optional[int]
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
        #if value is None:
        #    raise TypeError("Invalid NULL sequence no.")
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
        return {TYPE: AMQPTypes.symbol, VALUE: value.encode('utf-8')}

    @staticmethod
    def decode(value):
        # type: (Optional[str]) -> List[str]
        return value.decode('utf-8')


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
            fields[VALUE].append(({TYPE: AMQPTypes.symbol, VALUE: key}, data))
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        decoded = {}
        if value:
            for key, data in value:
                decoded[key] = data
        return decoded


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
        encoded = ({TYPE: AMQPTypes.ulong, VALUE: 29}, [])
        try:
            encoded[1].append({TYPE: AMQPTypes.symbol, VALUE: value.condition.value})
        except AttributeError:
            encoded[1].append({TYPE: AMQPTypes.symbol, VALUE: value.condition})
        encoded[1].append(value.description or None)
        encoded[1].append(FieldsField.encode(value.info))
        return encoded

    @staticmethod
    def decode(value):
        # type: (Optional[Tuple(int, List[Any])]) -> Optional[AMQPError]
        decoded = None
        if value and value[0] == 29:
            condition = value[1][0]
            description = value[1][1] if len(value[1]) > 1 else None
            info = value[1][2] if len(value[1]) > 2 else {}
            try:
                if b":link:" in condition:
                    condition = LinkErrorCondition(condition)
                    if condition == LinkErrorCondition.Redirect:
                        decoded = AMQPLinkRedirect(condition, description=description, info=info)
                    else:
                        decoded = AMQPLinkError(condition, description=description, info=info)
                elif b":session:" in condition:
                    condition = SessionErrorCondition(condition)
                    decoded = AMQPSessionError(condition, description=description, info=info)
                elif b":connection:" in condition:
                    condition = ConnectionErrorCondition(condition)
                    if condition == ConnectionErrorCondition.Redirect:
                        decoded = AMQPConnectionRedirect(condition, description=description, info=info)
                    else:
                        decoded = AMQPConnectionError(condition, description=description, info=info)
                else:
                    condition = ErrorCondition(condition)
                    decoded = AMQPError(condition, description=description, info=info)
            except ValueError:
                decoded = AMQPError(condition, description=description, info=info)
        return decoded


class AnnotationsField(object):
    """The annotations type is a map where the keys are restricted to be of type symbol or of type ulong.

    All ulong keys, and all symbolic keys except those beginning with ”x-” are reserved.
    On receiving an annotations map containing keys or values which it does not recognize, and for which the
    key does not begin with the string 'x-opt-' an AMQP container MUST detach the link with the not-implemented
    amqp-error.

    <type name="annotations" class="restricted" source="map"/>
    """

    @staticmethod
    def encode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        fields = {TYPE: AMQPTypes.map, VALUE:[]}
        for key, data in value.items():
            if isinstance(key, int):
                fields[VALUE].append(({TYPE: AMQPTypes.ulong, VALUE: key}, data))
            else:
                if isinstance(key, six.text_type):
                    key = key.encode('utf-8')
                fields[VALUE].append(({TYPE: AMQPTypes.symbol, VALUE: key}, data))
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        decoded = {}
        if value:
            for key, data in value:
                decoded[key] = data
        return decoded


class AppPropertiesField(object):
    """The application-properties section is a part of the bare message used for structured application data.

    <type name="application-properties" class="restricted" source="map" provides="section">
        <descriptor name="amqp:application-properties:map" code="0x00000000:0x00000074"/>
    </type>

    Intermediaries may use the data within this structure for the purposes of ﬁltering or routing.
    The keys of this map are restricted to be of type string (which excludes the possibility of a null key)
    and the values are restricted to be of simple types only, that is (excluding map, list, and array types).
    """

    @staticmethod
    def encode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        fields = {TYPE: AMQPTypes.map, VALUE:[]}
        for key, data in value.items():
            fields[VALUE].append(({TYPE: AMQPTypes.string, VALUE: key}, data))
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        decoded = {}
        if value:
            for key, data in value:
                decoded[key] = data
        return decoded


class MessageIDField(object):
    """
    <type name="message-id-ulong" class="restricted" source="ulong" provides="message-id"/>
    <type name="message-id-uuid" class="restricted" source="uuid" provides="message-id"/>
    <type name="message-id-binary" class="restricted" source="binary" provides="message-id"/>
    <type name="message-id-string" class="restricted" source="string" provides="message-id"/>
    """
    @staticmethod
    def encode(value):
        # type: (Any) -> Dict[str, Union[int, uuid.UUID, bytes, str]]
        if isinstance(value, int):
            return {TYPE: AMQPTypes.ulong, VALUE: value}
        elif isinstance(value, uuid.UUID):
            return {TYPE: AMQPTypes.uuid, VALUE: value}
        elif isinstance(value, six.binary_type):
            return {TYPE: AMQPTypes.binary, VALUE: value}
        elif isinstance(value, six.text_type):
            return {TYPE: AMQPTypes.string, VALUE: value}
        raise TypeError("Unsupported Message ID type.")

    @staticmethod
    def decode(value):
        # type: (Any) -> Any
        return value


class SASLCodeField(object):
    """Codes to indicate the outcome of the sasl dialog.

    <type name="sasl-code" class="restricted" source="ubyte">
        <choice name="ok" value="0"/>
        <choice name="auth" value="1"/>
        <choice name="sys" value="2"/>
        <choice name="sys-perm" value="3"/>
        <choice name="sys-temp" value="4"/>
    </type>
    """

    @staticmethod
    def encode(value):
        # type: (SASLCode) -> Dict[str, Any]
        return {TYPE: AMQPTypes.ubyte, VALUE: struct.pack('>B', value.value)}

    @staticmethod
    def decode(value):
        # type: (bytes) -> bytes
        #as_int = struct.unpack('>B', value)[0]
        return SASLCode(value)


class TerminusDurabilityField(object):
    """Durability policy for a terminus.

    <type name="terminus-durability" class="restricted" source="uint">
        <choice name="none" value="0"/>
        <choice name="configuration" value="1"/>
        <choice name="unsettled-state" value="2"/>
    </type>
    
    Determines which state of the terminus is held durably.
    """

    @staticmethod
    def encode(value):
        # type: (TerminusDurability) -> Dict[str, Union[AMQPTypes, int]]
        return {TYPE: AMQPTypes.uint, VALUE: value.value}

    @staticmethod
    def decode(value):
        # type: (int) -> TerminusDurability
        return TerminusDurability(value)


class ExpiryPolicyField(object):
    """Expiry policy for a terminus.

    <type name="terminus-expiry-policy" class="restricted" source="symbol">
        <choice name="link-detach" value="link-detach"/>
        <choice name="session-end" value="session-end"/>
        <choice name="connection-close" value="connection-close"/>
        <choice name="never" value="never"/>
    </type>
    
    Determines when the expiry timer of a terminus starts counting down from the timeout
    value. If the link is subsequently re-attached before the terminus is expired, then the
    count down is aborted. If the conditions for the terminus-expiry-policy are subsequently
    re-met, the expiry timer restarts from its originally conﬁgured timeout value.
    """

    @staticmethod
    def encode(value):
        # type: (ExpiryPolicy) -> Dict[str, Union[AMQPTypes, bytes]]
        return {TYPE: AMQPTypes.symbol, VALUE: value.value}

    @staticmethod
    def decode(value):
        # type: (bytes) -> ExpiryPolicy
        return ExpiryPolicy(value)


class DistributionModeField(object):
    """Link distribution policy.

    <type name="std-dist-mode" class="restricted" source="symbol" provides="distribution-mode">
        <choice name="move" value="move"/>
        <choice name="copy" value="copy"/>
    </type>
    
    Policies for distributing messages when multiple links are connected to the same node.
    """

    @staticmethod
    def encode(value):
        # type: (DistributionMode) -> Dict[str, Union[AMQPTypes, bytes]]
        return {TYPE: AMQPTypes.symbol, VALUE: value.value}

    @staticmethod
    def decode(value):
        # type: (bytes) -> DistributionMode
        return DistributionMode(value)


class NodePropertiesField(object):
    """Properties of a node.

    <type name="node-properties" class="restricted" source="fields"/>
    
    A symbol-keyed map containing properties of a node used when requesting creation or reporting
    the creation of a dynamic node. The following common properties are deﬁned::
    
        - `lifetime-policy`: The lifetime of a dynamically generated node. Deﬁnitionally, the lifetime will
          never be less than the lifetime of the link which caused its creation, however it is possible to extend
          the lifetime of dynamically created node using a lifetime policy. The value of this entry MUST be of a type
          which provides the lifetime-policy archetype. The following standard lifetime-policies are deﬁned below:
          delete-on-close, delete-on-no-links, delete-on-no-messages or delete-on-no-links-or-messages.
        
        - `supported-dist-modes`: The distribution modes that the node supports. The value of this entry MUST be one or
          more symbols which are valid distribution-modes. That is, the value MUST be of the same type as would be valid
          in a ﬁeld deﬁned with the following attributes:
          type="symbol" multiple="true" requires="distribution-mode"
    """

    @staticmethod
    def encode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        # TODO
        fields = {TYPE: AMQPTypes.map, VALUE:[]}
        # fields[{TYPE: AMQPTypes.symbol, VALUE: b'lifetime-policy'}] = {
        #     TYPE: AMQPTypes.described,
        #     VALUE: (
        #         {TYPE: AMQPTypes.ulong, VALUE: value['lifetime_policy'].value},
        #         {TYPE: AMQPTypes.list, VALUE: []}
        #     )
        # }
        # fields[{TYPE: AMQPTypes.symbol, VALUE: b'supported-dist-modes'}] = {}
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        return value or {}


class FilterSetField(object):
    """A set of predicates to ﬁlter the Messages admitted onto the Link.

    <type name="filter-set" class="restricted" source="map"/>

    A set of named ﬁlters. Every key in the map MUST be of type symbol, every value MUST be either null or of a
    described type which provides the archetype ﬁlter. A ﬁlter acts as a function on a message which returns a
    boolean result indicating whether the message can pass through that ﬁlter or not. A message will pass
    through a ﬁlter-set if and only if it passes through each of the named ﬁlters. If the value for a given key is
    null, this acts as if there were no such key present (i.e., all messages pass through the null ﬁlter).

    Filter types are a deﬁned extension point. The ﬁlter types that a given source supports will be indicated
    by the capabilities of the source.
    """

    @staticmethod
    def encode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        if not value:
            return {TYPE: AMQPTypes.null, VALUE: None}
        fields = {TYPE: AMQPTypes.map, VALUE:[]}
        for name, data in value.items():
            if data is None:
                described_filter = {TYPE: AMQPTypes.null, VALUE: None}
            else:
                if isinstance(name, six.text_type):
                    name = name.encode('utf-8')
                descriptor, filter_value = data
                described_filter = {
                    TYPE: AMQPTypes.described,
                    VALUE: (
                        {TYPE: AMQPTypes.symbol, VALUE: descriptor},
                        filter_value
                    )
                }
            fields[VALUE].append(({TYPE: AMQPTypes.symbol, VALUE: name}, described_filter))
        return fields

    @staticmethod
    def decode(value):
        # type: (Optional[Dict[str, Any]]) -> Dict[str, Any]
        return value or {}


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
    FieldDefinition.message_format: MessageFormatField,
    FieldDefinition.ietf_language_tag: IETFLanguageTagField,
    FieldDefinition.fields: FieldsField,
    FieldDefinition.error: ErrorField,
    FieldDefinition.annotations: AnnotationsField,
    FieldDefinition.message_id: MessageIDField,
    FieldDefinition.app_properties: AppPropertiesField,
    FieldDefinition.sasl_code: SASLCodeField,
    FieldDefinition.terminus_durability: TerminusDurabilityField,
    FieldDefinition.expiry_policy: ExpiryPolicyField,
    FieldDefinition.distribution_mode: DistributionModeField,
    FieldDefinition.node_properties: NodePropertiesField,
    FieldDefinition.filter_set: FilterSetField,
}
