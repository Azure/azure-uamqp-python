#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------
import logging
import timeit


def test_timeit_receive_message_batch():
    SETUP_CODE = '''
import time
import os
from uamqp import ReceiveClient
from uamqp.authentication import SASLPlainAuth

eventhub_config = {}
eventhub_config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
eventhub_config['event_hub'] = os.environ['EVENT_HUB_NAME']
eventhub_config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
eventhub_config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
eventhub_config['consumer_group'] = "$Default"
eventhub_config['partition'] = "0"

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
receive_client = ReceiveClient(hostname, source, sas_auth, idle_timeout=10, link_credit=300)
receive_client.open()
while not receive_client.client_ready():
    time.sleep(0.05)
        '''

    TEST_CODE = '''
receive_client.receive_message_batch(max_batch_size=1000)
    '''

    time = timeit.timeit(TEST_CODE, setup=SETUP_CODE, number=20)
    print(time)
    logging.info(time)


if __name__ == '__main__':
    test_timeit_receive_message_batch()
