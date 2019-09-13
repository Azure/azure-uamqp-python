#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum

class AMQPErrorCondition(Enum):
    """
    <type name="amqp-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="internal-error" value="amqp:internal-error"/>
        <choice name="not-found" value="amqp:not-found"/>
        <choice name="unauthorized-access" value="amqp:unauthorized-access"/>
        <choice name="decode-error" value="amqp:decode-error"/>
        <choice name="resource-limit-exceeded" value="amqp:resource-limit-exceeded"/>
        <choice name="not-allowed" value="amqp:not-allowed"/>
        <choice name="invalid-field" value="amqp:invalid-field"/>
        <choice name="not-implemented" value="amqp:not-implemented"/>
        <choice name="resource-locked" value="amqp:resource-locked"/>
        <choice name="precondition-failed" value="amqp:precondition-failed"/>
        <choice name="resource-deleted" value="amqp:resource-deleted"/>
        <choice name="illegal-state" value="amqp:illegal-state"/>
        <choice name="frame-size-too-small" value="amqp:frame-size-too-small"/>
    </type>
    """
    InternalError = b"amqp:internal-error"
    NotFDound = b"amqp:not-found"
    UnauthorizedAccess = b"amqp:unauthorized-access"
    DecodeError = b"amqp:decode-error"
    ResourceLimitExceeded = b"amqp:resource-limit-exceeded"
    NotAllowed = b"amqp:not-allowed"
    InvalidField = b"amqp:invalid-field"
    NotImplemented = b"amqp:not-implemented"
    ResourceLocked = b"amqp:resource-locked"
    PreconditionFailed = b"amqp:precondition-failed"
    ResourceDeleted = b"amqp:resource-deleted"
    IllegalState = b"amqp:illegal-state"
    FrameSizeTooSmall = b"amqp:frame-size-too-small"


class ConnectionErrorCondition(Enum):
    """
    <type name="connection-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="connection-forced" value="amqp:connection:forced"/>
        <choice name="framing-error" value="amqp:connection:framing-error"/>
        <choice name="redirect" value="amqp:connection:redirect"/>
    </type>
    """
    ConnectionForced = b"amqp:connection:forced"
    FramingError = b"amqp:connection:framing-error"
    Redirect = b"amqp:connection:redirect"


class SessionErrorCondition(Enum):
    """
    <type name="session-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="window-violation" value="amqp:session:window-violation"/>
        <choice name="errant-link" value="amqp:session:errant-link"/>
        <choice name="handle-in-use" value="amqp:session:handle-in-use"/>
        <choice name="unattached-handle" value="amqp:session:unattached-handle"/>
    </type>
    """
    WindowViolation = b"amqp:session:window-violation"
    ErrantLink = b"amqp:session:errant-link"
    HandleInUse = b"amqp:session:handle-in-use"
    UnattachedHandle = b"amqp:session:unattached-handle"


class LinkErrorCondition(Enum):
    """
    <type name="link-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="detach-forced" value="amqp:link:detach-forced"/>
        <choice name="transfer-limit-exceeded" value="amqp:link:transfer-limit-exceeded"/>
        <choice name="message-size-exceeded" value="amqp:link:message-size-exceeded"/>
        <choice name="redirect" value="amqp:link:redirect"/>
        <choice name="stolen" value="amqp:link:stolen"/>
    </type>
    """
    DetachForced = b"amqp:link:detach-forced"
    TransferLimitExceeded = b"amqp:link:transfer-limit-exceeded"
    MessageSizeExceeded = b"amqp:link:message-size-exceeded"
    Redirect = b"amqp:link:redirect"
    Stolen = b"amqp:link:stolen"


class AMQPError(object):
    """
    <type name="error" class="composite" source="list">
        <descriptor name="amqp:error:list" code="0x00000000:0x0000001d"/>
        <field name="condition" type="symbol" requires="error-condition" mandatory="true"/>
        <field name="description" type="string"/>
        <field name="info" type="fields"/>
    </type>
    """

    header = 29

    def __init__(self, condition, description=None, info=None):
        self.condition = condition
        self.description = description
        self.info = info

    @classmethod
    def from_response(cls, data):
        if not data:
            raise ValueError("Received invalid AMQP error response.")
        condition = data[0][VALUE]
        description = data[1][VALUE] if len(data) > 1 else None
        info = data[2][VALUE] if len(data) > 2 else None
        return cls(condition, description=description, info=info)