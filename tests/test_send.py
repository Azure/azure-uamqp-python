#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os

from uamqp import SendClient
from uamqp.sasl import SASLPlainCredential
from uamqp.message import Message


logging.basicConfig(level=logging.INFO)


def send_single_message_to_target_partition(config):
    hostname = config['hostname']
    target = "amqps://{}/{}/Partitions/{}".format(config['hostname'], config['event_hub'], config['partition'])
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    send_client = SendClient(hostname, target, auth=creds, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    send_client.send_message(Message(data=b'Test'))
    send_client.close()


def send_single_message_to_partition(config):
    hostname = config['hostname']
    target = "amqps://{}/{}".format(config['hostname'], config['event_hub'])
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    send_client = SendClient(hostname, target, auth=creds, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    send_client.send_message(Message(data=b'Test'))
    send_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    send_single_message_to_target_partition(config)
