#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import logging
import os
import asyncio

from uamqp.aio import SendClient
from uamqp.message import Message, BatchMessage, Header, Properties
from uamqp.utils import add_batch
from uamqp.authentication import SASLPlainAuth, SASTokenAuth


logging.basicConfig(level=logging.INFO)


async def send_single_message_to_partition_sasl_plain_auth(eventhub_config):
    hostname = eventhub_config['hostname']
    target = "amqps://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    auth = SASLPlainAuth(authcid=eventhub_config['key_name'], passwd=eventhub_config['access_key'])
    send_client = SendClient(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    await send_client.open_async()
    while not await send_client.client_ready_async():
        await asyncio.sleep(0.05)
    await send_client.send_message_async(Message(data=[b'Test']))
    await send_client.close_async()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    asyncio.run(send_single_message_to_partition_sasl_plain_auth(config))
