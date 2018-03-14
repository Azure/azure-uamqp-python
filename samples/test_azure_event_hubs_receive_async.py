#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import os
import pytest
import asyncio

import uamqp
from uamqp import address
from uamqp import authentication
from uamqp import async as a_uamqp


log = logging.getLogger(__name__)


async def on_message_received(message):
    annotations = message.message_annotations
    log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
    log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
    log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
    log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
    log.info("Message format: {}".format(message._message.message_format))
    log.info("{}".format(list(message.get_data())))


@pytest.mark.asyncio
async def test_event_hubs_callback_receive_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = a_uamqp.ReceiveClientAsync(source, auth=sas_auth, timeout=50, prefetch=10)
    await receive_client.receive_messages_async(on_message_received)


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

    receive_client = a_uamqp.ReceiveClientAsync(source, auth=plain_auth, timeout=50)
    await receive_client.receive_messages_async(on_message_received)


@pytest.mark.asyncio
async def test_event_hubs_iter_receive_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = a_uamqp.ReceiveClientAsync(source, debug=False, auth=sas_auth, timeout=100, prefetch=10)
    async for message in receive_client.receive_messages_iter_async():
        annotations = message.message_annotations
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))


@pytest.mark.asyncio
async def test_event_hubs_batch_receive_async(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    async with a_uamqp.ReceiveClientAsync(source, debug=False, auth=sas_auth, timeout=100, prefetch=10) as receive_client:
        message_batch = await receive_client.receive_message_batch_async(10)
        log.info("got batch: {}".format(len(message_batch)))
        for message in message_batch:
            annotations = message.message_annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        next_batch = await receive_client.receive_message_batch_async(10)
        log.info("got another batch: {}".format(len(next_batch)))
        for message in next_batch:
            annotations = message.message_annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        next_batch = await receive_client.receive_message_batch_async(20)
        log.info("got another batch: {}".format(len(next_batch)))
        for message in next_batch:
            annotations = message.message_annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
