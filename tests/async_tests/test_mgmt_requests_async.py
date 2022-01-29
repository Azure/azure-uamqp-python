#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os
import asyncio
import pytest

from uamqp.aio import AMQPClientAsync
from uamqp.message import Message, BatchMessage, Header, Properties
from uamqp.authentication import SASLPlainAuth
from uamqp.aio._authentication_async import SASTokenAuthAsync
from uamqp.error import AMQPException, ErrorCondition


logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
async def test_mgmt_request_get_eventhub_properties_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    amqp_client = AMQPClientAsync(hostname, auth=auth, idle_timeout=10, network_trace=True)
    await amqp_client.open_async()
    while not await amqp_client.client_ready_async():
        await asyncio.sleep(0.05)
    mgmt_msg = Message(application_properties={"name": eventhub_config["event_hub"]})
    response = await amqp_client.mgmt_request_async(
        mgmt_msg,
        operation="READ",
        operation_type="com.microsoft:eventhub",
        status_code_field=b'status-code',
        status_description_field=b'status-description'
    )
    assert response.application_properties[b"status-code"] < 400
    dict_value_body = response.value
    assert dict_value_body[b'name'] == eventhub_config["event_hub"].encode()
    assert dict_value_body[b'partition_count'] > 0
    assert dict_value_body[b'partition_ids']
    assert dict_value_body[b'created_at']
    assert dict_value_body[b'type'] == b'com.microsoft:eventhub'
    await amqp_client.close_async()

    # Error case
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    amqp_client = AMQPClientAsync(hostname, auth=sas_auth, idle_timeout=10, network_trace=True)
    await amqp_client.open_async()
    while not await amqp_client.client_ready_async():
        await asyncio.sleep(0.05)
    mgmt_msg = Message(application_properties={"name": eventhub_config["event_hub"]})
    error = None
    try:
        await amqp_client.mgmt_request_async(
            mgmt_msg,
            operation="DELETE",
            operation_type="com.microsoft:eventhub",
            status_code_field=b'status-code',
            status_description_field=b'status-description'
        )
    except Exception as exc:
        error = exc

    assert isinstance(error, AMQPException)
    assert error.condition == ErrorCondition.NotAllowed.value
    await amqp_client.close_async()


@pytest.mark.asyncio
async def test_mgmt_request_get_partition_properties_async(eventhub_config):
    hostname = eventhub_config['hostname']
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    amqp_client = AMQPClientAsync(hostname, auth=auth, idle_timeout=10, network_trace=True)
    await amqp_client.open_async()
    while not await amqp_client.client_ready_async():
        await asyncio.sleep(0.05)
    mgmt_msg = Message(
        application_properties={
            "name": eventhub_config["event_hub"],
            "partition": eventhub_config["partition"]
        }
    )

    response = await amqp_client.mgmt_request_async(
        mgmt_msg,
        operation="READ",
        operation_type="com.microsoft:partition",
        status_code_field=b'status-code',
        status_description_field=b'status-description'
    )
    assert response.application_properties[b"status-code"] < 400
    dict_value_body = response.value
    assert b'is_partition_empty' in dict_value_body
    assert b'last_enqueued_time_utc' in dict_value_body
    assert b'last_enqueued_offset' in dict_value_body
    assert b'last_enqueued_sequence_number' in dict_value_body
    assert b'begin_sequence_number' in dict_value_body
    assert dict_value_body[b'type'] == b'com.microsoft:partition'
    assert dict_value_body[b'partition'] == eventhub_config['partition'].encode()
    assert dict_value_body[b'name'] == eventhub_config['event_hub'].encode()
    await amqp_client.close_async()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    asyncio.run(test_mgmt_request_get_eventhub_properties_async(config))
    asyncio.run(test_mgmt_request_get_partition_properties_async(config))
