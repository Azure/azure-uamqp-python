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


log = get_logger(logging.INFO)


def _build_iothub_amqp_endpoint_from_target(target):
    hub_name = target['hostname'].split('.')[0]
    endpoint = "{}@sas.root.{}".format(target['key_name'], hub_name)
    endpoint = quote_plus(endpoint)
    sas_token = SasTokenAuthentication(target['hostname'], target['key_name'],
                                       target['access_key'], time() + 360).generate_sas_token()
    endpoint = endpoint + ":{}@{}".format(quote_plus(sas_token), target['hostname'])
    return endpoint


def _receive_message(receive_client, target):
    try:
        batch = receive_client.receive_message_batch(max_batch_size=10)
    except errors.LinkRedirect as redirect:
        new_auth = authentication.SASLPlain(redirect.hostname, target['key_name'], target['access_key'])
        #new_auth = authentication.SASTokenAuth.from_shared_access_key(redirect.address.decode('utf-8'), target['key_name'], target['access_key'])
        receive_client.redirect(redirect, new_auth)
        batch = receive_client.receive_message_batch(max_batch_size=10)

    while batch:
        log.info("Got batch: {}".format(len(batch)))
        assert len(batch) <= 10
        for message in batch:
            annotations = message.annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        batch = receive_client.receive_message_batch(max_batch_size=10)


def test_iothub_client_receive_sync(live_iothub_config):
    operation = '/messages/events/ConsumerGroups/{}/Partitions/{}'.format(
        live_iothub_config['consumer_group'],
        live_iothub_config['partition'])
    endpoint = _build_iothub_amqp_endpoint_from_target(live_iothub_config)

    source = 'amqps://' + endpoint + operation
    log.info("Source: {}".format(source))
    receive_client = uamqp.ReceiveClient(source, debug=False, timeout=5000, prefetch=50)
    try:
        log.info("Created client, receiving...")
        _receive_message(receive_client, live_iothub_config)
    except Exception as e:
        print(e)
        raise
    finally:
        receive_client.close()
    log.info("Finished receiving")


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['IOTHUB_HOSTNAME']
    config['device'] = os.environ['IOTHUB_DEVICE']
    config['key_name'] = os.environ['IOTHUB_SAS_POLICY']
    config['access_key'] = os.environ['IOTHUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    test_iothub_client_receive_sync(config)
