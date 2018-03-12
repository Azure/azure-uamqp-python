#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import os
import pytest

import uamqp
from uamqp import address
from uamqp import authentication


log = logging.getLogger(__name__)


hostname = os.environ.get("EVENT_HUB_HOSTNAME")
event_hub = os.environ.get("EVENT_HUB_NAME")
key_name = os.environ.get("EVENT_HUB_SAS_POLICY")
access_key = os.environ.get("EVENT_HUB_SAS_KEY")
consumer_group = "$Default"
partition = "0"
max_messages = 10


def test_event_hubs_simple_receive():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)

    message = uamqp.receive_message(source, auth=plain_auth)
    log.info("Received: {}".format(message))


def test_event_hubs_client_receive():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)
    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=1000)
    log.info("Created client, receiving...")
    
    receiver = receive_client.receive_messages_iter()
    count = 0
    for message in receiver:
        if count >= max_messages:
            break
        annotations = message.message_annotations
        log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
        log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
        log.info("Message format: {}".format(message._message.message_format))
        log.info("{}".format(list(message.get_data())))
        count += 1
    log.info("Finished receiving")


def test_event_hubs_callback_receive():
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

    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)

    receive_client = uamqp.ReceiveClient(source, auth=plain_auth, timeout=5)
    log.info("Created client, receiving...")
    
    receive_client.receive_messages(on_message_received)
    log.info("Finished receiving")


def test_event_hubs_filter_receive():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)
    source_url = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)
    source = address.Source(source_url)
    source.set_filter(b"amqp.annotation.x-opt-enqueuedtimeutc > 1518731960545")

    receive_client = uamqp.ReceiveClient(source, auth=plain_auth, prefetch=1, timeout=1000)
    log.info("Created client, receiving...")
    
    receiver = receive_client.receive_messages_iter()
    count = 0
    for message in receiver:
        if count >= max_messages:
            break
        annotations = message.message_annotations
        log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
        log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
        log.info("Message format: {}".format(message._message.message_format))
        log.info("{}".format(list(message.get_data())))
        count += 1
    log.info("Finished receiving")


if __name__ == "__main__":
    azure_event_hub_simple_receive()
