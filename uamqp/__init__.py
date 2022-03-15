# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

__version__ = "2.0.0a1"


from uamqp._connection import Connection
from uamqp._transport import SSLTransport

from uamqp.client import AMQPClient, ReceiveClient, SendClient
