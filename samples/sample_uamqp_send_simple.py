#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import uamqp
from uamqp import authentication


uri = os.environ.get("AMQP_SERVICE_URI")
key_name = os.environ.get("AMQP_SERVICE_KEY_NAME")
access_key = os.environ.get("AMQP_SERVICE_ACCESS_KEY")

def uamqp_send_simple():
    msg_content = b"Hello world"

    parsed_uri = urlparse(uri)
    plain_auth = authentication.SASLPlain(parsed_uri.hostname, key_name, access_key)

    uamqp.send_message(uri, msg_content, auth=plain_auth)
    print("Message sent!")

if __name__ == "__main__":
    uamqp_send_simple()
