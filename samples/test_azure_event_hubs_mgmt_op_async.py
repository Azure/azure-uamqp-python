#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import asyncio
import pytest
import sys

import uamqp
from uamqp import async as a_uamqp
from uamqp import authentication


def get_logger(level):
    azure_logger = logging.getLogger("azure")
    azure_logger.setLevel(level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
    azure_logger.addHandler(handler)

    uamqp_logger = logging.getLogger("uamqp")
    uamqp_logger.setLevel(logging.DEBUG)
    uamqp_logger.addHandler(handler)
    return azure_logger


log = get_logger(logging.INFO)


@pytest.mark.asyncio
async def test_event_hubs_mgmt_op_async(live_eventhub_config):

    plain_auth = authentication.SASLPlain(live_eventhub_config['hostname'], live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    async with uamqp.AMQPClientAsync(target, auth=plain_auth, debug=True) as send_client:
        mgmt_msg = uamqp.Message(application_properties={'name': live_eventhub_config['event_hub']})
        response = await send_client.mgmt_request_async(mgmt_msg, b'READ', op_type=b'com.microsoft:eventhub', status_code_field=b'status-code', description_fields=b'status-description')
        output = response.get_data()
        assert output['partition_ids'] == ["0", "1"]