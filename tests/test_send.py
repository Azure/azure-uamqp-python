#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os

from uamqp import SendClient
from uamqp.message import Message, BatchMessage
from uamqp.utils import add_batch
from uamqp.authentication import SASLPlainAuth, SASTokenAuth


logging.basicConfig(level=logging.INFO)


def send_single_message_to_target_partition_sasl_plain_auth(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    target = "amqps://{}/{}/Partitions/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'], live_eventhub_config['partition'])
    auth = SASLPlainAuth(authcid=live_eventhub_config['key_name'], passwd=live_eventhub_config['access_key'])
    send_client = SendClient(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    send_client.send_message(Message(data=[b'Test']))
    send_client.close()


def send_single_message_to_partition_sasl_plain_auth(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    auth = SASLPlainAuth(authcid=live_eventhub_config['key_name'], passwd=live_eventhub_config['access_key'])
    send_client = SendClient(hostname, target, auth=auth, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    send_client.send_message(Message(data=[b'Test']))
    send_client.close()


def send_message_to_partition_sas_auth(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=live_eventhub_config['key_name'],
        password=live_eventhub_config['access_key']
    )
    send_client = SendClient(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    send_client.send_message(Message(data=[b'Test']))
    send_client.close()


def send_batch_message_to_partition_sas_auth(live_eventhub_config):
    hostname = config['hostname']
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    target = "amqps://{}/{}".format(config['hostname'], config['event_hub'])
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=live_eventhub_config['key_name'],
        password=live_eventhub_config['access_key']
    )
    send_client = SendClient(hostname, target, auth=sas_auth, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)

    batch_message = BatchMessage()
    for _ in range(10):
        add_batch(batch_message, Message(data=[b'Test']))
    send_client.send_message(batch_message)
    send_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    send_single_message_to_partition_sasl_plain_auth(config)
    send_single_message_to_target_partition_sasl_plain_auth(config)
    send_message_to_partition_sas_auth(config)
    send_batch_message_to_partition_sas_auth(config)
