#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import logging
import os
import asyncio
import pytest

from uamqp.aio import ReceiveClientAsync, SASTokenAuthAsync
from uamqp.authentication import SASLPlainAuth


logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
async def test_receive_messages_sasl_plain_async(eventhub_config):
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
    receive_client = ReceiveClientAsync(hostname, source, sas_auth, idle_timeout=10, network_trace=True)
    await receive_client.open_async()
    while not await receive_client.client_ready_async():
        await asyncio.sleep(0.05)
    messages = await receive_client.receive_message_batch_async(max_batch_size=1)
    logging.info(len(messages))
    logging.info(messages[0])
    await receive_client.close_async()


@pytest.mark.asyncio
async def test_receive_messages_sas_auth_async(eventhub_config):
    hostname = eventhub_config['hostname']
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        eventhub_config['hostname'],
        eventhub_config['event_hub'],
        eventhub_config['consumer_group'],
        eventhub_config['partition']
    )
    sas_auth = SASTokenAuthAsync(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )
    receive_client = ReceiveClientAsync(hostname, source, auth=sas_auth, idle_timeout=10, network_trace=True)
    await receive_client.open_async()
    while not await receive_client.client_ready_async():
        await asyncio.sleep(0.05)
    messages = await receive_client.receive_message_batch_async(max_batch_size=1)
    logging.info(len(messages))
    logging.info(messages[0])
    await receive_client.close_async()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    asyncio.run(test_receive_messages_sasl_plain_async(config))
    asyncio.run(test_receive_messages_sas_auth_async(config))
