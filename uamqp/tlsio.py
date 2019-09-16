#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from .constants import TLS_MAJOR, TLS_MINOR, TLS_REVISION
from .performatives import Performative, _as_bytes


class TLSHeaderFrame(Performative):
    """SASL Header protocol negotiation."""

    NAME = "TLS-HEADER"
    CODE = b"AMQP\x02"

    def __init__(self, header=None, **kwargs):
        self.version = b"{}.{}.{}".format(TLS_MAJOR, TLS_MINOR, TLS_REVISION)
        self.header = self.CODE + _as_bytes(TLS_MAJOR) + _as_bytes(TLS_MINOR) + _as_bytes(TLS_REVISION)
        if header and header != self.header:
            raise ValueError("Mismatching AMQP TLS protocol version.")
        super(TLSHeaderFrame, self).__init__(**kwargs)
