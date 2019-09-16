#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import struct
from enum import Enum

from .types import AMQPTypes, TYPE, VALUE
from .constants import SASL_MAJOR, SASL_MINOR, SASL_REVISION, FIELD
from .performatives import Performative, _as_bytes


class SASLCode(Enum):
    #: Connection authentication succeeded.
    ok = 0
    #: Connection authentication failed due to an unspecified problem with the supplied credentials.
    auth = 1
    #: Connection authentication failed due to a system error.
    sys = 2
    #: Connection authentication failed due to a system error that is unlikely to be corrected without intervention.
    sys_perm = 3
    #: Connection authentication failed due to a transient system error.
    sys_temp = 4


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
        as_int = struct.unpack('>B', value)[0]
        return SASLCode(as_int)


class SASLHeaderFrame(Performative):
    """SASL Header protocol negotiation."""

    NAME = "SASL-HEADER"
    CODE = b"AMQP\x03"

    def __init__(self, header=None, **kwargs):
        self.version = b"{}.{}.{}".format(SASL_MAJOR, SASL_MINOR, SASL_REVISION)
        self.header = self.CODE + _as_bytes(SASL_MAJOR) + _as_bytes(SASL_MINOR) + _as_bytes(SASL_REVISION)
        if header and header != self.header:
            raise ValueError("Mismatching AMQP SASL protocol version.")
        super(SASLHeaderFrame, self).__init__(**kwargs)


class SASLMechanism(Performative):
    """Advertise available sasl mechanisms.

    dvertises the available SASL mechanisms that may be used for authentication.

    :param list(bytes) sasl_server_mechanisms: Supported sasl mechanisms.
        A list of the sasl security mechanisms supported by the sending peer.
        It is invalid for this list to be null or empty. If the sending peer does not require its partner to
        authenticate with it, then it should send a list of one element with its value as the SASL mechanism
        ANONYMOUS. The server mechanisms are ordered in decreasing level of preference.
    """
    NAME = 'SASL-MECHANISM'
    CODE = 0x00000040
    DEFINITION = {FIELD('sasl_server_mechanisms', AMQPTypes.symbol, True, None, True)}
    FRAME_TYPE = b'\x01'


class SASLInit(Performative):
    """Initiate sasl exchange.

    Selects the sasl mechanism and provides the initial response if needed.

    :param bytes mechanism: Selected security mechanism.
        The name of the SASL mechanism used for the SASL exchange. If the selected mechanism is not supported by
        the receiving peer, it MUST close the Connection with the authentication-failure close-code. Each peer
        MUST authenticate using the highest-level security profile it can handle from the list provided by the
        partner.
    :param bytes initial_response: Security response data.
        A block of opaque data passed to the security mechanism. The contents of this data are defined by the
        SASL security mechanism.
    :param str hostname: The name of the target host.
        The DNS name of the host (either fully qualified or relative) to which the sending peer is connecting. It
        is not mandatory to provide the hostname. If no hostname is provided the receiving peer should select a
        default based on its own configuration. This field can be used by AMQP proxies to determine the correct
        back-end service to connect the client to, and to determine the domain to validate the client's credentials
        against. This field may already have been specified by the server name indication extension as described
        in RFC-4366, if a TLS layer is used, in which case this field SHOULD benull or contain the same value.
        It is undefined what a different value to those already specific means.
    """
    NAME = 'SASL-INIT'
    CODE = 0x00000041
    DEFINITION = {
        FIELD('mechanism', AMQPTypes.symbol, True, None, False),
        FIELD('initial_response', AMQPTypes.binary, False, None, False),
        FIELD('hostname', AMQPTypes.string, False, None, False),
    }
    FRAME_TYPE = b'\x01'


class SASLChallenge(Performative):
    """Security mechanism challenge.

    Send the SASL challenge data as defined by the SASL specification.

    :param bytes challenge: Security challenge data.
        Challenge information, a block of opaque binary data passed to the security mechanism.
    """
    NAME = 'SASL-CHALLENGE'
    CODE = 0x00000042
    DEFINITION = {FIELD('challenge', AMQPTypes.binary, True, None, False)}
    FRAME_TYPE = b'\x01'


class SASLResponse(Performative):
    """Security mechanism response.

    Send the SASL response data as defined by the SASL specification.

    :param bytes response: Security response data.
    """
    NAME = 'SASL-RESPONSE'
    CODE = 0x00000043
    DEFINITION = {FIELD('response', AMQPTypes.binary, True, None, False)}
    FRAME_TYPE = b'\x01'


class SASLOutcome(Performative):
    """Indicates the outcome of the sasl dialog.

    This frame indicates the outcome of the SASL dialog. Upon successful completion of the SASL dialog the
    Security Layer has been established, and the peers must exchange protocol headers to either starta nested
    Security Layer, or to establish the AMQP Connection.

    :param SASLCode code: Indicates the outcome of the sasl dialog.
        A reply-code indicating the outcome of the SASL dialog.
    :param bytes additional_data: Additional data as specified in RFC-4422.
        The additional-data field carries additional data on successful authentication outcomeas specified by
        the SASL specification (RFC-4422). If the authentication is unsuccessful, this field is not set.
    """
    NAME = 'SASL-OUTCOME'
    CODE = 0x00000044
    DEFINITION = {
        FIELD('code', SASLCodeField, True, None, False),
        FIELD('additional_data', AMQPTypes.binary, False, None, False)
    }
    FRAME_TYPE = b'\x01'
