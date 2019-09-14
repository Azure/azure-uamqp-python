#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum


class ErrorCondition(Enum):
    """Shared error conditions

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
    InternalError = b"amqp:internal-error"  #: An internal error occurred. Operator intervention may be required to resume normaloperation.
    NotFDound = b"amqp:not-found"  #: A peer attempted to work with a remote entity that does not exist.
    UnauthorizedAccess = b"amqp:unauthorized-access"  #: A peer attempted to work with a remote entity to which it has no access due tosecurity settings.
    DecodeError = b"amqp:decode-error"  #: Data could not be decoded.
    ResourceLimitExceeded = b"amqp:resource-limit-exceeded"  #: A peer exceeded its resource allocation.
    NotAllowed = b"amqp:not-allowed"  #: The peer tried to use a frame in a manner that is inconsistent with the semantics defined in the specification.
    InvalidField = b"amqp:invalid-field"  #: An invalid field was passed in a frame body, and the operation could not proceed.
    NotImplemented = b"amqp:not-implemented"  #: The peer tried to use functionality that is not implemented in its partner.
    ResourceLocked = b"amqp:resource-locked"  #: The client attempted to work with a server entity to which it has no access because another client is working with it.
    PreconditionFailed = b"amqp:precondition-failed"  #: The client made a request that was not allowed because some precondition failed.
    ResourceDeleted = b"amqp:resource-deleted"  #: A server entity the client is working with has been deleted.
    IllegalState = b"amqp:illegal-state"  #: The peer sent a frame that is not permitted in the current state of the Session.
    FrameSizeTooSmall = b"amqp:frame-size-too-small"  #: The peer cannot send a frame because the smallest encoding of the performative with the currently valid values would be too large to fit within a frame of the agreed maximum frame size.


class ConnectionErrorCondition(Enum):
    """Symbols used to indicate connection error conditions.

    <type name="connection-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="connection-forced" value="amqp:connection:forced"/>
        <choice name="framing-error" value="amqp:connection:framing-error"/>
        <choice name="redirect" value="amqp:connection:redirect"/>
    </type>
    """
    ConnectionForced = b"amqp:connection:forced"  #: An operator intervened to close the Connection for some reason. The client may retry at some later date.
    FramingError = b"amqp:connection:framing-error"  #: A valid frame header cannot be formed from the incoming byte stream.
    Redirect = b"amqp:connection:redirect"  #: The container is no longer available on the current connection. The peer should attempt reconnection to the container using the details provided in the info map.


class SessionErrorCondition(Enum):
    """Symbols used to indicate session error conditions.

    <type name="session-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="window-violation" value="amqp:session:window-violation"/>
        <choice name="errant-link" value="amqp:session:errant-link"/>
        <choice name="handle-in-use" value="amqp:session:handle-in-use"/>
        <choice name="unattached-handle" value="amqp:session:unattached-handle"/>
    </type>
    """
    WindowViolation = b"amqp:session:window-violation"  #: The peer violated incoming window for the session.
    ErrantLink = b"amqp:session:errant-link"  #: Input was received for a link that was detached with an error.
    HandleInUse = b"amqp:session:handle-in-use"  #: An attach was received using a handle that is already in use for an attached Link.
    UnattachedHandle = b"amqp:session:unattached-handle"  #: A frame (other than attach) was received referencing a handle which is not currently in use of an attached Link.


class LinkErrorCondition(Enum):
    """Symbols used to indicate link error conditions.

    <type name="link-error" class="restricted" source="symbol" provides="error-condition">
        <choice name="detach-forced" value="amqp:link:detach-forced"/>
        <choice name="transfer-limit-exceeded" value="amqp:link:transfer-limit-exceeded"/>
        <choice name="message-size-exceeded" value="amqp:link:message-size-exceeded"/>
        <choice name="redirect" value="amqp:link:redirect"/>
        <choice name="stolen" value="amqp:link:stolen"/>
    </type>
    """
    DetachForced = b"amqp:link:detach-forced"  #: An operator intervened to detach for some reason.
    TransferLimitExceeded = b"amqp:link:transfer-limit-exceeded"  #: The peer sent more Message transfers than currently allowed on the link.
    MessageSizeExceeded = b"amqp:link:message-size-exceeded"  #: The peer sent a larger message than is supported on the link.
    Redirect = b"amqp:link:redirect"  #: The address provided cannot be resolved to a terminus at the current container.
    Stolen = b"amqp:link:stolen"  #: The link has been attached elsewhere, causing the existing attachment to be forcibly closed.


class AMQPError(object):
    """Details of an error.

    :param ~uamqp.ErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    """

    def __init__(self, condition, description=None, info=None):
        self.condition = condition
        self.description = description
        self.info = info


class AMQPConnectionError(AMQPError):
    """Details of a Connection-level error.

    :param ~uamqp.ConnectionErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    """


class AMQPConnectionRedirect(AMQPConnectionError):
    """Details of a Connection-level redirect response.

    The container is no longer available on the current connection.
    The peer should attempt reconnection to the container using the details provided.

    :param ~uamqp.ConnectionErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    :param str hostname: The hostname of the container.
        This is the value that should be supplied in the hostname field of the open frame, and during the SASL and
        TLS negotiation (if used).
    :param str network_host: The DNS hostname or IP address of the machine hosting the container.
    :param int port: The port number on the machine hosting the container.
    """

    def __init__(self, condition, description=None, info=None):
        self.hostname = info.get(b'hostname', b'').decode('utf-8')
        self.network_host = info.get(b'network-host', b'').decode('utf-8')
        self.port = int(info.get(b'port', 0))  # TODO: Default port
        super(AMQPConnectionRedirect, self).__init__(condition, description=description, info=info)


class AMQPSessionError(AMQPError):
    """Details of a Session-level error.

    :param ~uamqp.SessionErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    """


class AMQPLinkError(AMQPError):
    """Details of a Link-level error.

    :param ~uamqp.LinkErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    """

class AMQPLinkRedirect(AMQPLinkError):
    """Details of a Link-level redirect response.

    The address provided cannot be resolved to a terminus at the current container.
    The supplied information may allow the client to locate and attach to the terminus.

    :param ~uamqp.LinkErrorCondition condition: The error code.
    :param str description: A description of the error.
    :param info: A dictionary of additional data associated with the error.
    :param str hostname: The hostname of the container hosting the terminus.
        This is the value that should be supplied in the hostname field of the open frame, and during SASL
        and TLS negotiation (if used).
    :param str network_host: The DNS hostname or IP address of the machine hosting the container.
    :param int port: The port number on the machine hosting the container.
    :param str address: The address of the terminus at the container.
    """

    def __init__(self, condition, description=None, info=None):
        self.hostname = info.get(b'hostname', b'').decode('utf-8')
        self.network_host = info.get(b'network-host', b'').decode('utf-8')
        self.port = int(info.get(b'port', 0))  # TODO: Default port
        self.address = info.get(b'address', b'').decode('utf-8')
        super(AMQPLinkRedirect, self).__init__(condition, description=description, info=info)
