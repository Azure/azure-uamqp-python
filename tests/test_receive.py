#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os

from uamqp import ReceiveClient
from uamqp.endpoints import Source
from uamqp.authentication import SASLPlainAuth, SASTokenAuth
from uamqp.types import VALUE, TYPE, AMQPTypes
from uamqp.utils import amqp_long_value


logging.basicConfig(level=logging.INFO)


def test_receive_messages_sasl_plain(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        eventhub_config['hostname'],
        eventhub_config['event_hub'],
        eventhub_config['consumer_group'],
        eventhub_config['partition']
    )
    sas_auth = SASLPlainAuth(
        authcid=eventhub_config['key_name'],
        passwd=eventhub_config['access_key']
    )
    receive_client = ReceiveClient(hostname, source, sas_auth, idle_timeout=10, network_trace=True)
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    messages = receive_client.receive_message_batch(timeout=5)
    assert messages
    logging.info(len(messages))
    logging.info(messages[0])
    receive_client.close()


def test_receive_messages_sas_auth(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        eventhub_config['hostname'],
        eventhub_config['event_hub'],
        eventhub_config['consumer_group'],
        eventhub_config['partition']
    )
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    receive_client = ReceiveClient(hostname, source, auth=sas_auth, idle_timeout=10, network_trace=True)
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    messages = receive_client.receive_message_batch(max_batch_size=1)
    assert len(messages) == 1
    logging.info(len(messages))
    logging.info(messages[0])
    receive_client.close()


def test_receive_messages_with_customizations(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    starting_sequence = 2
    source = Source(
        address="amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
            eventhub_config['hostname'],
            eventhub_config['event_hub'],
            eventhub_config['consumer_group'],
            eventhub_config['partition']
        ),
        filters={
            "apache.org:selector-filter:string":
            (
                "apache.org:selector-filter:string",
                {TYPE: AMQPTypes.string, VALUE: "amqp.annotation.x-opt-sequence-number >= '2'".format(starting_sequence)}
            )
        }
    )
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    receive_client = ReceiveClient(
        hostname,
        source,
        auth=sas_auth,
        idle_timeout=10,
        network_trace=True,
        link_properties={b"com.microsoft:epoch": amqp_long_value(0)},
        desired_capabilities=[b"com.microsoft:enable-receiver-runtime-metric"],
    )
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    messages = receive_client.receive_message_batch(max_batch_size=1)
    assert len(messages)
    assert len(messages[0].delivery_annotations)
    assert messages[0].message_annotations[b'x-opt-sequence-number'] >= starting_sequence
    logging.info(len(messages))
    logging.info(messages[0])
    receive_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    test_receive_messages_sas_auth(config)
    test_receive_messages_sasl_plain(config)
    test_receive_messages_with_customizations(config)
