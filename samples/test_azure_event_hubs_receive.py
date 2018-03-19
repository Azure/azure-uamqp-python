#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import os
import pytest
import time
try:
    from urllib import quote_plus #Py2
except Exception:
    from urllib.parse import quote_plus

import uamqp
from uamqp import address
from uamqp import authentication


log = logging.getLogger(__name__)


def test_event_hubs_simple_receive(live_eventhub_config):
    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    message = uamqp.receive_message(source, auth=plain_auth)
    log.info("Received: {}".format(message))


def test_event_hubs_simple_batch_receive(live_eventhub_config):

    source = "amqps://{}:{}@{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        quote_plus(live_eventhub_config['key_name']),
        quote_plus(live_eventhub_config['access_key']),
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    messages = uamqp.receive_messages(source, batch_size=10)
    assert len(messages) == 10

    message = uamqp.receive_messages(source, batch_size=1)
    assert len(message) == 1


def test_event_hubs_single_batch_receive(live_eventhub_config):
    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    message = uamqp.receive_messages(source, auth=plain_auth, timeout=5000)
    assert len(message) == 300


def test_event_hubs_client_receive(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])
    with uamqp.ReceiveClient(source, auth=sas_auth, debug=False, timeout=50, prefetch=50) as receive_client:
        log.info("Created client, receiving...")
        batch = receive_client.receive_message_batch(batch_size=10)
        while batch:
            for message in batch:
                annotations = message.message_annotations
                log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
                log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
                log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
                log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
                log.info("Message format: {}".format(message._message.message_format))
                log.info("{}".format(list(message.get_data())))
            batch = receive_client.receive_message_batch(batch_size=10)
    log.info("Finished receiving")


def test_event_hubs_callback_receive(live_eventhub_config):
    def on_message_received(message):
        annotations = message.message_annotations
        log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
        log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
        log.info("Message format: {}".format(message._message.message_format))
        log.info("{}".format(list(message.get_data())))
        return message

    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClient(source, auth=plain_auth, timeout=50)
    log.info("Created client, receiving...")
    
    receive_client.receive_messages(on_message_received)
    log.info("Finished receiving")


def test_event_hubs_filter_receive(live_eventhub_config):
    if not live_eventhub_config['hostname']:
        pytest.skip("No live endpoint configured.")
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

    with uamqp.ReceiveClient(source, auth=plain_auth, timeout=50, prefetch=50) as receive_client:
        log.info("Created client, receiving...")
        batch = receive_client.receive_message_batch(batch_size=10)
        while batch:
            for message in batch:
                annotations = message.message_annotations
                log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
                log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
                log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
                log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
                log.info("Message format: {}".format(message._message.message_format))
                log.info("{}".format(list(message.get_data())))
            batch = receive_client.receive_message_batch(batch_size=10)
    log.info("Finished receiving")
