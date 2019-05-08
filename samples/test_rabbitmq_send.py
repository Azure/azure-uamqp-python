#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys
import datetime
import uuid
import pytest

import uamqp
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


def test_rabbitmq_client_send_sync(rabbit_mq_config):
    pytest.skip("Not working yet")
    uri = "amqp://{}/{}/".format(rabbit_mq_config['hostname'], rabbit_mq_config['path'])
    sas_auth = uamqp.authentication.SASLAnonymous(hostname=rabbit_mq_config['hostname'], port=5672)
    send_client = uamqp.SendClient(uri, auth=sas_auth, debug=False)
    try:
        message = uamqp.Message("content")
        send_client.queue_message(message)
        results = send_client.send_all_messages(close_on_done=False)
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    finally:
        send_client.close()

if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['RABBITMQ_HOSTNAME']
    config['path'] = os.environ['RABBITMQ_PATH']

    test_rabbitmq_client_send_sync(config)
