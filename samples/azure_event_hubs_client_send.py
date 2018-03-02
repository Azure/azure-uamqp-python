#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os

import uamqp
from uamqp import authentication


hostname = os.environ.get("EVENT_HUB_HOSTNAME")
event_hub = os.environ.get("EVENT_HUB_NAME")
key_name = os.environ.get("EVENT_HUB_KEY_NAME")
access_key = os.environ.get("EVENT_HUB_ACCESS_KEY")


def azure_event_hubs_client_send():
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    message = uamqp.Message(msg_content, application_properties=properties)

    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}/Partitions/1".format(hostname, event_hub)
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=True)

    send_client.queue_message(message)
    log.info("sending all messages")
    send_client.send_all_messages()
    log.info("finished sending")

if __name__ == "__main__":
    test_eh_client_send_sync()