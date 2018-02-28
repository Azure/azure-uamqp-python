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
consumer_group = "$Default"
partition = "0"


def azure_event_hub_simple_receive():
    plain_auth = authentication.SASLPlain(hostname, key_name, access_key)

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        hostname, event_hub, consumer_group, partition)

    message = uamqp.receive_message(source, auth=plain_auth)
    print("Received: {}".format(message))


if __name__ == "__main__":
    azure_event_hub_simple_receive()
