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


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.INFO)


def _generate_sas_token(uri, policy, key, expiry=None):
    if not expiry:
        expiry = time() + 3600  # Default to 1 hour.
    encoded_uri = quote_plus(uri)
    ttl = int(expiry)
    sign_key = '%s\n%d' % (encoded_uri, ttl)
    signature = b64encode(HMAC(b64decode(key), sign_key.encode('utf-8'), sha256).digest())
    result = {
        'sr': uri,
        'sig': signature,
        'se': str(ttl)}
    if policy:
        result['skn'] = policy
    return 'SharedAccessSignature ' + urlencode(result)


def _build_iothub_amqp_endpoint_from_target(target):
    hub_name = target['hostname'].split('.')[0]
    username = "{}@sas.root.{}".format(target['key_name'], hub_name)
    sas_token = _generate_sas_token(target['hostname'], target['key_name'],
                                    target['access_key'], time() + 360)
    return username, sas_token


def _receive_message(conn, source, auth):
    batch = []
    receive_client = uamqp.ReceiveClient(source, auth=auth, debug=False, timeout=5000, prefetch=50)
    try:
        receive_client.open(connection=conn)
        batch = receive_client.receive_message_batch(max_batch_size=10)
    except errors.LinkRedirect as redirect:
        return redirect
    finally:
        receive_client.close()
    return batch


def test_iothub_client_receive_sync(live_iothub_config):
    operation = '/messages/events/ConsumerGroups/{}/Partitions/{}'.format(
        live_iothub_config['consumer_group'],
        live_iothub_config['partition'])
    auth = authentication.SASLPlain(
        live_iothub_config['hostname'],
        *_build_iothub_amqp_endpoint_from_target(live_iothub_config))

    source = 'amqps://' + live_iothub_config['hostname'] + operation
    log.info("Source: {}".format(source))
    with uamqp.Connection(live_iothub_config['hostname'], auth, debug=False) as conn:
        result = _receive_message(conn, source, auth)
        new_auth = authentication.SASLPlain(
           result.hostname,
           live_iothub_config['key_name'],
           live_iothub_config['access_key'])
        conn.redirect(result, new_auth)
        result = _receive_message(conn, result.address, new_auth)
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
