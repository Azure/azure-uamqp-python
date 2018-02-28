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


def azure_event_hub_simple_send():

    msg_content = b"Hello world"
    
    uri = "sb://{}/{}".format(hostname, event_hub)
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)

    target = "amqps://{}/{}".format(hostname, event_hub)
    uamqp.send_message(target, msg_content, auth=sas_auth)

if __name__ == "__main__":
    azure_event_hub_simple_send()
