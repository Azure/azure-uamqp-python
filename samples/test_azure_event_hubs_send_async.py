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
from uamqp import async as a_uamqp
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
    send_client = a_uamqp.SendClientAsync(target, auth=plain_auth, debug=True)
    send_client.queue_message(message)
    results = await send_client.send_all_messages_async()
    assert not [m for m in results if m == uamqp.constants.MessageState.Failed]


@pytest.mark.asyncio
async def test_event_hubs_single_send_async(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = a_uamqp.SendClientAsync(target, auth=sas_auth, debug=False)
    await send_client.send_message_async(message, close_on_done=True)


@pytest.mark.asyncio
async def test_event_hubs_batch_send_async(live_eventhub_config):
    def data_generator():
        for i in range(5):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    message_batch = uamqp.message.BatchMessage(data_generator())

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = a_uamqp.SendClientAsync(target, auth=sas_auth, debug=False)

    send_client.queue_message(message_batch)
    results = await send_client.send_all_messages_async()
    assert not [m for m in results if m == uamqp.constants.MessageState.Failed]
