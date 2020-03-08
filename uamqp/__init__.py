#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

__version__ = "2.0.0a1"


from .connection import Connection
from ._transport import SSLTransport

from .client import SendClient, ReceiveClient
