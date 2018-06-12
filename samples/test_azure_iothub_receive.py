#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys
try:
    from urllib import quote #Py2
except Exception:
    from urllib.parse import quote

import uamqp
from uamqp import utils
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

def _build_iothub_amqp_endpoint_from_target(target):
    hub_name = target['hostname'].split('.')[0]
    endpoint = "{}@sas.root.{}".format(target['key_name'], hub_name)
    endpoint = quote(endpoint)
    sas_token = utils.create_sas_token(
        target['key_name'].encode('utf-8'), 
        target['access_key'].encode('utf-8'), 
        target['hostname'].encode('utf-8'))
    endpoint = endpoint + ":{}@{}".format(quote(sas_token), target['hostname'])
    return endpoint


def test_iothub_client_receive_sync(live_iothub_config):
    operation = '/messages/events/'
    endpoint = _build_iothub_amqp_endpoint_from_target(live_iothub_config)
    source = 'amqps://' + endpoint + operation
    log.info("Source: {}".format(source))
    with uamqp.ReceiveClient(source, debug=True, timeout=50, prefetch=50) as receive_client:
        log.info("Created client, receiving...")
        batch = receive_client.receive_message_batch(max_batch_size=10)
        while batch:
            log.info("Got batch: {}".format(len(batch)))
            assert len(batch) <= 10
            for message in batch:
                annotations = message.annotations
                log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
            batch = receive_client.receive_message_batch(max_batch_size=10)
    log.info("Finished receiving")


if __name__ == '__main__':
    config = {}
    config['hostname'] = s.environ['IOTHUB_HOSTNAME']
    config['device'] = os.environ['IOTHUB_DEVICE']
    config['key_name'] = os.environ['IOTHUB_SAS_POLICY']
    config['access_key'] = os.environ['IOTHUB_SAS_KEY']

    test_iothub_client_receive_sync(config)