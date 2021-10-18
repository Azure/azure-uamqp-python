#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os

from uamqp import AMQPClient
from uamqp.message import Message, BatchMessage, Header, Properties
from uamqp.utils import add_batch
from uamqp.authentication import SASLPlainAuth, SASTokenAuth


logging.basicConfig(level=logging.INFO)


def test_mgmt_request_get_eventhub_properties(eventhub_config):
    hostname = eventhub_config['hostname']
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    amqp_client = AMQPClient(hostname, auth=auth, idle_timeout=10, network_trace=True)
    amqp_client.open()
    while not amqp_client.client_ready():
        time.sleep(0.05)
    mgmt_msg = Message(application_properties={"name": eventhub_config["event_hub"]})
    response = amqp_client.mgmt_request(
        mgmt_msg,
        operation="READ",
        operation_type="com.microsoft:eventhub",
        status_code_field=b'status-code',
        status_description_field=b'status-description'
    )
    assert response["application_properties"][b"status-code"] < 400
    dict_value_body = response["value"]
    assert dict_value_body[b'name'] == eventhub_config["event_hub"].encode()
    assert dict_value_body[b'partition_count'] > 0
    assert dict_value_body[b'partition_ids']
    assert dict_value_body[b'created_at']
    assert dict_value_body[b'type'] == b'com.microsoft:eventhub'


def test_mgmt_request_get_partition_properties(eventhub_config):
    hostname = eventhub_config['hostname']
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    amqp_client = AMQPClient(hostname, auth=auth, idle_timeout=10, network_trace=True)
    amqp_client.open()
    while not amqp_client.client_ready():
        time.sleep(0.05)
    mgmt_msg = Message(
        application_properties={
            "name": eventhub_config["event_hub"],
            "partition": eventhub_config["partition"]
        }
    )

    response = amqp_client.mgmt_request(
        mgmt_msg,
        operation="READ",
        operation_type="com.microsoft:partition",
        status_code_field=b'status-code',
        status_description_field=b'status-description'
    )
    assert response["application_properties"][b"status-code"] < 400
    dict_value_body = response["value"]
    assert b'is_partition_empty' in dict_value_body
    assert b'last_enqueued_time_utc' in dict_value_body
    assert b'last_enqueued_offset' in dict_value_body
    assert b'last_enqueued_sequence_number' in dict_value_body
    assert b'begin_sequence_number' in dict_value_body
    assert dict_value_body[b'type'] == b'com.microsoft:partition'
    assert dict_value_body[b'partition'] == eventhub_config['partition'].encode()
    assert dict_value_body[b'name'] == eventhub_config['event_hub'].encode()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    test_mgmt_request_get_eventhub_properties(config)
    test_mgmt_request_get_partition_properties(config)
