#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import struct
from enum import Enum

from ._transport import SSLTransport
from .types import AMQPTypes, TYPE, VALUE
from .constants import SASL_MAJOR, SASL_MINOR, SASL_REVISION, FIELD, SASLCode
from .performatives import (
    SASLHeaderFrame,
    SASLOutcome,
    SASLResponse,
    SASLChallenge,
    SASLInit
)


_SASL_FRAME_TYPE = b'\x01'


class SASLPlainCredential(object):
    """PLAIN SASL authentication mechanism.
    See https://tools.ietf.org/html/rfc4616 for details
    """

    mechanism = b'PLAIN'

    def __init__(self, authcid, passwd, authzid=None):
        self.authcid = authcid
        self.passwd = passwd
        self.authzid = authzid

    def start(self):
        if self.authzid:
            login_response = self.authzid.encode('utf-8')
        else:
            login_response = b''
        login_response += b'\0'
        login_response += self.authcid.encode('utf-8')
        login_response += b'\0'
        login_response += self.passwd.encode('utf-8')
        return login_response


class SASLAnonymousCredential(object):
    """ANONYMOUS SASL authentication mechanism.
    See https://tools.ietf.org/html/rfc4505 for details
    """

    mechanism = b'ANONYMOUS'

    def start(self):
        return b''


class SASLExternalCredential(object):
    """EXTERNAL SASL mechanism.
    Enables external authentication, i.e. not handled through this protocol.
    Only passes 'EXTERNAL' as authentication mechanism, but no further
    authentication data.
    """

    mechanism = b'EXTERNAL'

    def start(self):
        return b''


class SASLTransport(SSLTransport):

    def __init__(self, host, credential, connect_timeout=None, ssl=None, **kwargs):
        self.credential = credential
        super(SASLTransport, self).__init__(host, connect_timeout=connect_timeout, ssl=ssl, **kwargs)

    def negotiate(self):
        with self.block():
            self.send_frame(0, SASLHeaderFrame(), frame_type=_SASL_FRAME_TYPE)
            _, returned_header = self.receive_frame()
            if not isinstance(returned_header, SASLHeaderFrame):
                raise ValueError("Mismatching AMQP header protocol. Excpected code: {}, received code: {}".format(
                    SASLHeaderFrame._code, returned_header._code))

            _, supported_mechansisms = self.receive_frame(verify_frame_type=1)
            if self.credential.mechanism not in supported_mechansisms.sasl_server_mechanisms:
                raise ValueError("Unsupported SASL credential type: {}".format(self.credential.mechanism))
            sasl_init = SASLInit(
                mechanism=self.credential.mechanism,
                initial_response=self.credential.start(),
                hostname=self.host)
            self.send_frame(0, sasl_init, frame_type=_SASL_FRAME_TYPE)

            _, next_frame = self.receive_frame(verify_frame_type=1)
            if not isinstance(next_frame, SASLOutcome):
                raise NotImplementedError("Unsupported SASL challenge")
            if next_frame.code == SASLCode.Ok:
                return
            else:
                raise ValueError("SASL negotiation failed.\nOutcome: {}\nDetails: {}".format(
                    next_frame.code, next_frame.additional_data))