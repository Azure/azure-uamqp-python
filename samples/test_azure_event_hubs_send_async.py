#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import asyncio
import pytest

import uamqp
from uamqp import async as a_uamqp
from uamqp import authentication


log = logging.getLogger(__name__)


hostname = os.environ.get("EVENT_HUB_HOSTNAME")
event_hub = os.environ.get("EVENT_HUB_NAME")
key_name = os.environ.get("EVENT_HUB_SAS_POLICY")
access_key = os.environ.get("EVENT_HUB_SAS_KEY")
batch_message_count = 500


async def event_hubs_client_send(send_client):
    await send_client.send_all_messages_async()


def test_event_hubs_client_send_async():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    loop = asyncio.get_event_loop()

    properties = {b"SendData", b"Property_String_Value_1"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, application_properties=properties)
    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)
    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = a_uamqp.SendClientAsync(target, auth=plain_auth, debug=False)
    loop.run_until_complete(event_hubs_client_send(send_client))


async def event_hubs_single_send(send_client, message):
    await send_client.send_message_async(message, close_on_done=True)


def test_event_hubs_single_send_async():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    loop = asyncio.get_event_loop()

    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = a_uamqp.SendClientAsync(target, auth=sas_auth, debug=False)
    loop.run_until_complete(event_hubs_single_send(send_client, message))


async def event_hubs_batch_send(send_client):
    await send_client.send_all_messages_async()


def test_event_hubs_batch_send_async():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    def data_generator():
        for i in range(batch_message_count):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    loop = asyncio.get_event_loop()
    message_batch = uamqp.message.BatchMessage(data_generator())

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = a_uamqp.SendClientAsync(target, auth=sas_auth, debug=False)

    send_client.queue_message(message_batch)
    loop.run_until_complete(event_hubs_batch_send(send_client))


if __name__ == "__main__":
    test_event_hubs_client_send()