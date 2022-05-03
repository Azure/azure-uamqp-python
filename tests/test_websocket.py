# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from uamqp import ReceiveClient
from uamqp.authentication import SASTokenAuth
from  uamqp.constants import TransportType

def test_event_hubs_client_web_socket(eventhub_config):
    uri = "sb://{}/{}".format(eventhub_config['hostname'], eventhub_config['event_hub'])
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=eventhub_config['key_name'],
        password=eventhub_config['access_key']
    )

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        eventhub_config['hostname'],
        eventhub_config['event_hub'],
        eventhub_config['consumer_group'],
        eventhub_config['partition'])

    with ReceiveClient(eventhub_config['hostname'], source, auth=sas_auth, debug=False, timeout=5000, prefetch=50, transport_type=TransportType.AmqpOverWebsocket) as receive_client:
        receive_client.receive_message_batch(max_batch_size=10)
