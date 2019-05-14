#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import asyncio
import pytest
import sys

import uamqp
from uamqp import authentication


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.INFO)


@pytest.mark.asyncio
async def test_event_hubs_client_send_async(live_eventhub_config):
    properties = {b"SendData": b"Property_String_Value_1"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, application_properties=properties)
    plain_auth = authentication.SASLPlain(live_eventhub_config['hostname'], live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClientAsync(target, auth=plain_auth, debug=False)
    send_client.queue_message(message)
    results = await send_client.send_all_messages_async()
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]


@pytest.mark.asyncio
async def test_event_hubs_single_send_async(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClientAsync(target, auth=sas_auth, debug=False)
   
    for _ in range(10):
        message = uamqp.Message(msg_content, application_properties=annotations, annotations=annotations)
        await send_client.send_message_async(message)
    await send_client.close_async()


@pytest.mark.asyncio
async def test_event_hubs_async_sender_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClientAsync(target, auth=sas_auth, debug=False)
   
    for _ in range(10):
        message = uamqp.Message(msg_content, application_properties=annotations, annotations=annotations)
        send_client.send_message(message)
    send_client.close()


@pytest.mark.asyncio
async def test_event_hubs_client_send_multiple_async(live_eventhub_config):
    properties = {b"SendData": b"Property_String_Value_1"}
    msg_content = b"hello world"
    plain_auth = authentication.SASLPlain(live_eventhub_config['hostname'], live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    assert not plain_auth.consumed

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClientAsync(target, auth=plain_auth, debug=False)
    messages = []
    for i in range(10):
        messages.append(uamqp.Message(msg_content, application_properties=properties))
    send_client.queue_message(*messages)
    assert len(send_client.pending_messages) == 10
    results = await send_client.send_all_messages_async()
    assert len(results) == 10
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    assert plain_auth.consumed
    assert send_client.pending_messages == []


@pytest.mark.asyncio
async def test_event_hubs_batch_send_async(live_eventhub_config):
    for _ in range(10):
        def data_generator():
            for i in range(50):
                msg_content = "Hello world {}".format(i).encode('utf-8')
                yield msg_content

        message_batch = uamqp.message.BatchMessage(data_generator())

        uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
        sas_auth = authentication.SASTokenAsync.from_shared_access_key(uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

        target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
        send_client = uamqp.SendClientAsync(target, auth=sas_auth, debug=False)

        send_client.queue_message(message_batch)
        results = await send_client.send_all_messages_async()
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_event_hubs_single_send_async(config))
