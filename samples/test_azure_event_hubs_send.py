#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys

import uamqp
from uamqp import authentication


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.INFO)


def test_event_hubs_simple_send(live_eventhub_config):
    msg_content = b"Hello world"
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'],live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    uamqp.send_message(target, msg_content, auth=sas_auth)


def test_event_hubs_client_send_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    proxy_settings={'proxy_hostname':'127.0.0.1', 'proxy_port': 12345}
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'], http_proxy=proxy_settings)

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        header = uamqp.message.MessageHeader()
        header.durable = True
        props = uamqp.message.MessageProperties(message_id=b"message id")
        msg_content = b"hello world"
        message = uamqp.Message(
            msg_content,
            properties=props,
            header=header,
            application_properties=annotations,
            annotations=annotations)
        send_client.queue_message(message)
        results = send_client.send_all_messages(close_on_done=False)
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    send_client.close()


def test_event_hubs_single_send_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        message = uamqp.Message(msg_content, application_properties=annotations, annotations=annotations)
        send_client.send_message(message)
    send_client.close()


def test_event_hubs_batch_send_sync(live_eventhub_config):
    def data_generator():
        for i in range(50):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        message_batch = uamqp.message.BatchMessage(data_generator())
        send_client.queue_message(message_batch)
        results = send_client.send_all_messages(close_on_done=False)
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    send_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    test_event_hubs_client_send_sync(config)
