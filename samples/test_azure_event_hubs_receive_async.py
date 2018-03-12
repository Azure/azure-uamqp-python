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


hostname = os.environ.get("EVENT_HUB_HOSTNAME")
event_hub = os.environ.get("EVENT_HUB_NAME")
key_name = os.environ.get("EVENT_HUB_SAS_POLICY")
access_key = os.environ.get("EVENT_HUB_SAS_KEY")
consumer_group = "$Default"
partition = "0"
max_messages = 10


async def event_hubs_callback_receive(receive_client, on_message_received):
    await receive_client.receive_messages_async(on_message_received)


def test_event_hubs_callback_receive_async():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    def on_message_received(message):
        annotations = message.message_annotations
        log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
        log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
        log.info("Message format: {}".format(message._message.message_format))
        log.info("{}".format(list(message.get_data())))

    loop = asyncio.get_event_loop()
    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = a_uamqp.SASTokenAsync.from_shared_access_key(uri, key_name, access_key)
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)

    receive_client = a_uamqp.ReceiveClientAsync(source, auth=sas_auth, timeout=5)
    loop.run_until_complete(event_hubs_callback_receive(receive_client, on_message_received))


async def event_hubs_filter_receive(receive_client, on_message_received):
    await receive_client.receive_messages_async(on_message_received)


def test_event_hubs_filter_receive_async():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    def on_message_received(message):
        annotations = message.message_annotations
        log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
        log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
        log.info("Message format: {}".format(message._message.message_format))
        log.info("{}".format(list(message.get_data())))

    loop = asyncio.get_event_loop()
    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)
    source_url = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)
    source = address.Source(source_url)
    source.set_filter(b"amqp.annotation.x-opt-enqueuedtimeutc > 1518731960545")

    receive_client = a_uamqp.ReceiveClientAsync(source, auth=plain_auth, timeout=5)
    loop.run_until_complete(event_hubs_filter_receive(receive_client, on_message_received))


if __name__ == "__main__":
    azure_event_hub_simple_receive()
