#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uamqp
from uamqp import authentication


uri = os.environ.get("AMQP_SERVICE_URI")
key_name = os.environ.get("AMQP_SERVICE_KEY_NAME")
access_key = os.environ.get("AMQP_SERVICE_ACCESS_KEY")

def uamqp_send_simple():

    msg_content = b"Hello world"
    
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(uri, key_name, access_key)
    uamqp.send_message(uri, msg_content, auth=sas_auth)

if __name__ == "__main__":
    uamqp_send_simple()