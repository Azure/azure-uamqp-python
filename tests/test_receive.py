#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import logging
import os

from uamqp import ReceiveClient
from uamqp.authentication import SASLPlainAuth, SASTokenAuth


logging.basicConfig(level=logging.INFO)


def receive_messages_sasl_plain(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition']
    )
    sas_auth = SASLPlainAuth(
        authcid=live_eventhub_config['key_name'],
        passwd=live_eventhub_config['access_key']
    )
    receive_client = ReceiveClient(hostname, source, auth=sas_auth, idle_timeout=10, network_trace=True)
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    meassages = receive_client.receive_message_batch(max_batch_size=1)
    logging.info(len(meassages))
    logging.info(meassages[0])
    receive_client.close()


def receive_messages_sas_auth(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition']
    )
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=live_eventhub_config['key_name'],
        password=live_eventhub_config['access_key']
    )
    receive_client = ReceiveClient(hostname, source, auth=sas_auth, idle_timeout=10, network_trace=True)
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    meassages = receive_client.receive_message_batch(max_batch_size=1)
    logging.info(len(meassages))
    logging.info(meassages[0])
    receive_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    receive_messages_sas_auth(config)
