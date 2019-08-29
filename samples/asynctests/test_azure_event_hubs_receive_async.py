#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import os
import pytest
import asyncio
import sys

import uamqp
from uamqp import address
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


def on_message_received(message):
    annotations = message.annotations
    log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
    return message


@pytest.mark.asyncio
async def test_event_hubs_callback_async_receive(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClientAsync(source, auth=sas_auth, timeout=10, prefetch=10)
    log.info("Created client, receiving...")
    await receive_client.receive_messages_async(on_message_received)
    log.info("Finished receiving")


@pytest.mark.asyncio
async def test_event_hubs_filter_receive_async(live_eventhub_config):
    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source_url = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])
    source = address.Source(source_url)
    source.set_filter(b"amqp.annotation.x-opt-enqueuedtimeutc > 1518731960545")

    receive_client = uamqp.ReceiveClientAsync(source, auth=plain_auth, timeout=50)
    await receive_client.receive_messages_async(on_message_received)


@pytest.mark.asyncio
async def test_event_hubs_iter_receive_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClientAsync(source, debug=False, auth=sas_auth, timeout=3000, prefetch=10)
    count = 0
    message_generator = receive_client.receive_messages_iter_async()
    async for message in message_generator:
        log.info("No. {} : {}".format(message.annotations.get(b'x-opt-sequence-number'), message))
        count += 1
        if count >= 10:
            log.info("Got {} messages. Breaking.".format(count))
            message.accept()
            break
    count = 0
    async for message in message_generator:
        count += 1
        if count >= 10:
            log.info("Got {} more messages. Shutting down.".format(count))
            message.accept()
            break
    await receive_client.close_async()


@pytest.mark.asyncio
async def test_event_hubs_batch_receive_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    async with uamqp.ReceiveClientAsync(source, debug=False, auth=sas_auth, timeout=3000, prefetch=10) as receive_client:
        message_batch = await receive_client.receive_message_batch_async(10)
        log.info("got batch: {}".format(len(message_batch)))
        for message in message_batch:
            annotations = message.annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        next_batch = await receive_client.receive_message_batch_async(10)
        log.info("got another batch: {}".format(len(next_batch)))
        for message in next_batch:
            annotations = message.annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        next_batch = await receive_client.receive_message_batch_async(10)
        log.info("got another batch: {}".format(len(next_batch)))
        for message in next_batch:
            annotations = message.annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))


@pytest.mark.asyncio
async def test_event_hubs_shared_connection_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'])

    async with uamqp.ConnectionAsync(live_eventhub_config['hostname'], sas_auth, debug=False) as conn:
        partition_0 = uamqp.ReceiveClientAsync(source + "0", debug=False, auth=sas_auth, timeout=3000, prefetch=10)
        partition_1 = uamqp.ReceiveClientAsync(source + "1", debug=False, auth=sas_auth, timeout=3000, prefetch=10)
        await partition_0.open_async(connection=conn)
        await partition_1.open_async(connection=conn)
        tasks = [
            partition_0.receive_message_batch_async(1),
            partition_1.receive_message_batch_async(1)
        ]
        try:
            messages = await asyncio.gather(*tasks)
            assert len(messages[0]) == 1 and len(messages[1]) == 1
        except:
            raise
        finally:
            await partition_0.close_async()
            await partition_1.close_async()

async def receive_ten(partition, receiver):
    messages = []
    count = 0
    while count < 10:
        print("Receiving {} on partition {}".format(count, partition))
        batch = await receiver.receive_message_batch_async(1)
        print("Received {} messages on partition {}".format(len(batch), partition))
        messages.extend(batch)
        count += 1
    print("Finished receiving on partition {}".format(partition))
    return messages

@pytest.mark.asyncio
async def test_event_hubs_multiple_receiver_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth_a = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    sas_auth_b = authentication.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'])

    partition_0 = uamqp.ReceiveClientAsync(source + "0", debug=False, auth=sas_auth_a, timeout=3000, prefetch=10)
    partition_1 = uamqp.ReceiveClientAsync(source + "1", debug=False, auth=sas_auth_b, timeout=3000, prefetch=10)
    try:
        await partition_0.open_async()
        await partition_1.open_async()
        tasks = [
            receive_ten("0", partition_0),
            receive_ten("1", partition_1)
        ]
        messages = await asyncio.gather(*tasks)
        assert len(messages) == 2
        assert len(messages[0]) >= 10
        assert len(messages[1]) >= 10
        print(messages)
    finally:
        await partition_0.close_async()
        await partition_1.close_async()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_event_hubs_iter_receive_async(config))
