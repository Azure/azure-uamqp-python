#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys
from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC
from time import time
from uuid import uuid4
try:
    from urllib import quote, quote_plus, urlencode #Py2
except Exception:
    from urllib.parse import quote, quote_plus, urlencode

import uamqp
from uamqp import utils, errors
from uamqp import authentication


### IotHub CLI Extension SAS token implementation

class SasTokenAuthentication():
    """
    Shared Access Signature authorization for Azure IoT Hub.
    Args:
        uri (str): Uri of target resource.
        shared_access_policy_name (str): Name of shared access policy.
        shared_access_key (str): Shared access key.
        expiry (int): Expiry of the token to be generated. Input should
            be seconds since the epoch, in UTC. Default is an hour later from now.
    """
    def __init__(self, uri, shared_access_policy_name, shared_access_key, expiry=None):
        self.uri = uri
        self.policy = shared_access_policy_name
        self.key = shared_access_key
        if expiry is None:
            self.expiry = time() + 3600  # Default expiry is an hour later
        else:
            self.expiry = expiry

    def generate_sas_token(self):
        """
        Create a shared access signiture token as a string literal.
        Returns:
            result (str): SAS token as string literal.
        """
        encoded_uri = quote_plus(self.uri)
        ttl = int(self.expiry)
        sign_key = '%s\n%d' % (encoded_uri, ttl)
        signature = b64encode(HMAC(b64decode(self.key), sign_key.encode('utf-8'), sha256).digest())
        result = {
            'sr': self.uri,
            'sig': signature,
            'se': str(ttl)
        }

        if self.policy:
            result['skn'] = self.policy

        return 'SharedAccessSignature ' + urlencode(result)


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.DEBUG)


def _build_iothub_amqp_endpoint_from_target(target):
    hub_name = target['hostname'].split('.')[0]
    endpoint = "{}@sas.root.{}".format(target['key_name'], hub_name)
    endpoint = quote_plus(endpoint)
    sas_token = SasTokenAuthentication(target['hostname'], target['key_name'],
                                       target['access_key'], time() + 360).generate_sas_token()
    endpoint = endpoint + ":{}@{}".format(quote_plus(sas_token), target['hostname'])
    return endpoint


def test_iot_hub_send(live_iothub_config):
    msg_content = b"hello world"
    msg_props = uamqp.message.MessageProperties()
    msg_props.to = '/devices/{}/messages/devicebound'.format(live_iothub_config['device'])
    msg_props.message_id = str(uuid4())
    message = uamqp.Message(msg_content, properties=msg_props)

    operation = '/messages/devicebound'
    endpoint = _build_iothub_amqp_endpoint_from_target(live_iothub_config)

    target = 'amqps://' + endpoint + operation
    log.info("Target: {}".format(target))

    send_client = uamqp.SendClient(target, debug=True)
    send_client.queue_message(message)
    send_client.send_all_messages()
    log.info("Message sent.")

if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['IOTHUB_HOSTNAME']
    config['device'] = os.environ['IOTHUB_DEVICE']
    config['key_name'] = os.environ['IOTHUB_SAS_POLICY']
    config['access_key'] = os.environ['IOTHUB_SAS_KEY']

    test_iot_hub_send(config)


