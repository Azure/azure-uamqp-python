#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging

import uamqp
from uamqp import authentication


log = logging.getLogger(__name__)


hostname = os.environ.get("EVENT_HUB_HOSTNAME")
event_hub = os.environ.get("EVENT_HUB_NAME")
key_name = os.environ.get("EVENT_HUB_SAS_POLICY")
access_key = os.environ.get("EVENT_HUB_SAS_KEY")
batch_message_count = 500


def test_event_hubs_simple_receive():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    msg_content = b"Hello world"
    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)
    target = "amqps://{}/{}".format(hostname, event_hub)
    uamqp.send_message(target, msg_content, auth=sas_auth)


def test_event_hubs_client_send():
    if not hostname:
        pytest.skip("No live endpoint configured.")

    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    send_client.queue_message(message)
    send_client.send_all_messages()


def test_event_hubs_single_send():
    if not hostname:
        pytest.skip("No live endpoint configured.")

    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, annotations=annotations)

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    send_client.send_message(message, close_on_done=True)


def test_event_hubs_batch_send():
    if not hostname:
        pytest.skip("No live endpoint configured.")
    def data_generator():
        for i in range(batch_message_count):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    message_batch = uamqp.message.BatchMessage(data_generator())

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)

    send_client.queue_message(message_batch)
    send_client.send_all_messages()


if __name__ == "__main__":
    test_event_hubs_client_send()