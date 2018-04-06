#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys

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


def test_event_hubs_mgmt_op(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    with uamqp.AMQPClient(target, auth=sas_auth, debug=True) as send_client:
        mgmt_msg = uamqp.Message(application_properties={'name': live_eventhub_config['event_hub']})
        response = send_client.mgmt_request(
            mgmt_msg,
            b'READ',
            op_type=b'com.microsoft:eventhub',
            status_code_field=b'status-code',
            description_fields=b'status-description')
        output = response.get_data()
        assert output['partition_ids'] == ["0", "1"]
