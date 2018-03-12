#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import sys

from uamqp import c_uamqp
from uamqp.message import Message, BatchMessage
from uamqp.address import Source, Target

from uamqp.connection import Connection
from uamqp.session import Session
from uamqp.client import SendClient, ReceiveClient
from uamqp.sender import MessageSender
from uamqp.receiver import MessageReceiver

try:
    from uamqp.async import ConnectionAsync
    from uamqp.async import SessionAsync
    from uamqp.async import MessageSenderAsync
    from uamqp.async import MessageReceiverAsync
    from uamqp.async import SendClientAsync, ReceiveClientAsync
except (SyntaxError, ImportError):
    pass  # Async not supported.


__version__ = "0.1.0a2"


_logger = logging.getLogger(__name__)
_is_win = sys.platform.startswith('win')
#c_uamqp.set_custom_logger()


def send_message(target, data, auth=None, debug=False):
    message = data if isinstance(data, Message) else Message(data)
    send_client = SendClient(target, auth=auth, debug=debug)
    send_client.queue_message(message)
    send_client.send_all_messages()


def receive_message(source, auth=None):
    receiver = receive_messages(source, auth=auth, prefetch=1, max_count=1)
    messages = list(receiver)
    return messages[0]


def receive_messages(source, timeout=0, auth=None, prefetch=None, max_count=None, debug=False):
    receive_client = ReceiveClient(source, auth=auth, timeout=timeout, prefetch=prefetch, debug=debug, max_count=max_count)
    return receive_client.receive_messages_iter()


def initialize_platform():
    if _is_win:
        c_uamqp.platform_init()
    else:
        c_uamqp.tlsio_openssl_init()


def deinitialize_platform():
    if _is_win:
        c_uamqp.platform_deinit()
    else:
        c_uamqp.tlsio_openssl_deinit()


def get_platform_info(self):
    return str(c_uamqp.get_info())
