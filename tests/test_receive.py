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
    meassages = receive_client.receive_message_batch(max_batch_size=1000)
    logging.info(len(meassages))
    logging.info(meassages[0])
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
    meassages = receive_client.receive_message_batch(max_batch_size=1000)
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

    test_receive_messages_sas_auth(config)
    test_receive_messages_sasl_plain(config)
