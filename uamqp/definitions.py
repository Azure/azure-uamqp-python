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
    ConnectionErrorCondition,
    AMQPSessionError,
    SessionErrorCondition,
    AMQPLinkError,
    LinkErrorCondition)


ENCODE_FIELDS = {
    FieldDefinition.role: None,
    FieldDefinition.sender_settle_mode: None,
    FieldDefinition.receiver_settle_mode: None,
    FieldDefinition.handle: None,
    FieldDefinition.seconds: None,
    FieldDefinition.milliseconds: encode_milliseconds,
    FieldDefinition.delivery_tag: None,
    FieldDefinition.delivery_number: None,
    FieldDefinition.transfer_number: None,
    FieldDefinition.sequence_no: None,
    FieldDefinition.message_format: None,
    FieldDefinition.ietf_language_tag: encode_ietf_language_tag,
    FieldDefinition.fields: encode_fields,
    FieldDefinition.error: encode_error,
}


DECODE_FIELDS = {
    FieldDefinition.role: None,
    FieldDefinition.sender_settle_mode: None,
    FieldDefinition.receiver_settle_mode: None,
    FieldDefinition.handle: None,
    FieldDefinition.seconds: None,
    FieldDefinition.milliseconds: decode_milliseconds,
    FieldDefinition.delivery_tag: None,
    FieldDefinition.delivery_number: None,
    FieldDefinition.transfer_number: None,
    FieldDefinition.sequence_no: None,
    FieldDefinition.message_format: None,
    FieldDefinition.ietf_language_tag: decode_ietf_language_tag,
    FieldDefinition.fields: decode_fields,
    FieldDefinition.error: decode_errpr,
}


def encode_milliseconds(value):
    # type: (timedelta) -> Dict[str, Any]
    """A duration measured in milliseconds.

    <type name="milliseconds" class="restricted" source="uint"/>
    """
    if value is None:
        return {TYPE: AMQPTypes.null, VALUE: None}
    milliseconds = int(value.microseconds/1000.0)
    return {TYPE: AMQPTypes.uint, VALUE: milliseconds}


def decode_milliseconds(value):
    # type: (Dict[str, Any]) -> timedelta
    """A duration measured in milliseconds.

    <type name="milliseconds" class="restricted" source="uint"/>
    """
    return timedelta(milliseconds=value[VALUE])


def encode_ietf_language_tag(value):
    # type: (str) -> Dict[str, Any]
    """An IETF language tag as defined by BCP 47.

    IETF language tags are abbreviated language codes as defined in the IETF Best Current PracticeBCP-47
    (http://www.rfc-editor.org/rfc/bcp/bcp47.txt) (incorporating  RFC-5646
    (http://www.rfc-editor.org/rfc/rfc5646.txt)). A list of registered subtags is maintained in the IANA
    Language SubtagRegistry (http://www.iana.org/assignments/language-subtag-registry). All AMQP implementations
    should understand at the least the IETF language tagen-US(note thatthis uses a hyphen separator, not an
    underscore).
    
    <type name="ietf-language-tag" class="restricted" source="symbol"/>
    """
    if not value:
        return {TYPE: AMQPTypes.null, VALUE: None}
    tag = ",".join(value).encode('utf-8')
    return {TYPE: AMQPTypes.symbol, VALUE: tag}


def decode_ietf_language_tag(value):
    # type: (str) -> Dict[str, Any]
    """An IETF language tag as defined by BCP 47.

    IETF language tags are abbreviated language codes as defined in the IETF Best Current PracticeBCP-47
    (http://www.rfc-editor.org/rfc/bcp/bcp47.txt) (incorporating  RFC-5646
    (http://www.rfc-editor.org/rfc/rfc5646.txt)). A list of registered subtags is maintained in the IANA
    Language SubtagRegistry (http://www.iana.org/assignments/language-subtag-registry). All AMQP implementations
    should understand at the least the IETF language tagen-US(note thatthis uses a hyphen separator, not an
    underscore).
    
    <type name="ietf-language-tag" class="restricted" source="symbol"/>
    """
    if value:
        return value.decode('utf-8').split(',')
    return []


def encode_fields(value):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """A mapping from field name to value.
    
    The fields type is a map where the keys are restricted to be of type symbol (this excludes the possibility
    of a null key).  There is no further restriction implied by the fields type on the allowed values for the
    entries or the set of allowed keys.

    <type name="fields" class="restricted" source="map"/>
    """
    if not value:
        return {TYPE: AMQPTypes.null, VALUE: None}
    fields = {TYPE: AMQPTypes.map, VALUE:[]}
    for key, data in value.items():
        if isinstance(key, six.text_type):
            key = key.encode('utf-8')
        fields[VALUE].append(({TYPE: AMQPTypes.symbol, VALUE: key}, value))
    return fields


def decode_fields(value):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """A mapping from field name to value.
    
    The fields type is a map where the keys are restricted to be of type symbol (this excludes the possibility
    of a null key).  There is no further restriction implied by the fields type on the allowed values for the
    entries or the set of allowed keys.

    <type name="fields" class="restricted" source="map"/>
    """
    return value if value else {}


def encode_error(value):
    # type: (AMQPError) -> Dict[str, Any]
    """
    Details of an error.

    <type name="error" class="composite" source="list">
        <descriptor name="amqp:error:list" code="0x00000000:0x0000001d"/>
        <field name="condition" type="symbol" requires="error-condition" mandatory="true"/>
        <field name="description" type="string"/>
        <field name="info" type="fields"/>
    </type>
    """
    if not value:
        return {TYPE: AMQPTypes.null, VALUE: None}
    value = {TYPE: AMQPTypes.described, VALUE: ({TYPE: AMQPTypes.ulong, VALUE: 29}, [])}
    value[VALUE][1].append()


def decode_error(value):
    # type: (Tuple(int, List[Any])) -> Optional[AMQPError]
    """Details of an error.

    <type name="error" class="composite" source="list">
        <descriptor name="amqp:error:list" code="0x00000000:0x0000001d"/>
        <field name="condition" type="symbol" requires="error-condition" mandatory="true"/>
        <field name="description" type="string"/>
        <field name="info" type="fields"/>
    </type>
    """
    if value and value[0] == 29:
        condition = value[1][0].decode('utf-8')
        description = value[1][1].decode('utf-8') if len(value[1]) > 1 else None
        info = value[1][2] if len(value[1]) > 2 else None
        try:
            if ":link:" in condition:
                condition = LinkErrorCondition(condition)
                return AMQPLinkError(condition, description=description, info=info)
            if ":session:" in condition:
                condition = SessionErrorCondition(condition)
                return AMQPSessionError(condition, description=description, info=info)
            if ":connection:" in condition:
                condition = ConnectionErrorCondition(condition)
                return AMQPConnectionError(condition, description=description, info=info)
            condition = ErrorCondition(condition)
        except ValueError:
            pass
        return AMQPError(condition, description=description, info=info)
    return None
