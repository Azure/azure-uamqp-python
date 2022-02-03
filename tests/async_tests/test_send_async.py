#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import logging
import os
import asyncio
import pytest

from uamqp.aio import SendClientAsync, SASTokenAuthAsync
from uamqp.message import Message, BatchMessage, Header, Properties
from uamqp.utils import add_batch
from uamqp.authentication import SASLPlainAuth


logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
async def test_send_single_message_to_target_partition_sasl_plain_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    target = "amqps://{}/{}/Partitions/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'], eventhub_config['partition'])
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    send_client = SendClientAsync(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)
    await send_client.send_message_async(Message(data=[b'Test']))
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_single_large_message_to_target_partition_sasl_plain_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    target = "amqps://{}/{}/Partitions/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'], eventhub_config['partition'])
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    send_client = SendClientAsync(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)

    await send_client.send_message_async(Message(data=[b'Test' * 1024 * 128]))
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_single_message_to_partition_sasl_plain_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    send_client = SendClientAsync(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)
    await send_client.send_message_async(Message(data=[b'Test']))
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_message_to_partition_sas_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    send_client = SendClientAsync(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)
    await send_client.send_message_async(Message(data=[b'Test']))
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_message_with_properties_to_partition_sas_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    send_client = SendClientAsync(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)

    await send_client.send_message_async(
        Message(
            data=[b'Test'],
            delivery_annotations={"my_key": "my_value"},
            message_annotations={"msganno": "msganno"},
            application_properties={"testapp": "testappvalue"}
        )
    )
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_batch_message_to_partition_sas_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    send_client = SendClientAsync(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)

    batch_message = BatchMessage(data=[])
    for _ in range(10):
        add_batch(batch_message, Message(data=[b'Test']))
    await send_client.send_message_async(batch_message)
    await send_client.close_async()


@pytest.mark.asyncio
async def test_send_large_batch_message_to_partition_sas_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    send_client = SendClientAsync(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)

    batch_message = BatchMessage(data=[])
    for i in range(10 * 1024):
        add_batch(batch_message, Message(data=[b'Test']))
    await send_client.send_message_async(batch_message)
    await send_client.close_async()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    asyncio.run(test_send_single_message_to_target_partition_sasl_plain_auth_async(config))
    asyncio.run(test_send_single_large_message_to_target_partition_sasl_plain_auth_async(config))
    asyncio.run(test_send_single_message_to_partition_sasl_plain_auth_async(config))
    asyncio.run(test_send_message_to_partition_sas_auth_async(config))
    asyncio.run(test_send_message_with_properties_to_partition_sas_auth_async(config))
    asyncio.run(test_send_batch_message_to_partition_sas_auth_async(config))
    asyncio.run(test_send_large_batch_message_to_partition_sas_auth_async(config))
