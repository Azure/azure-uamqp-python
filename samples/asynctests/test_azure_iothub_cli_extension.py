# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import logging
import pytest
from datetime import datetime

import uamqp


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


logger = get_logger(logging.INFO)


def _get_iot_conn_str(live_iothub_config):
    result = {}
    result['cs'] = "HostName={};SharedAccessKeyName={};SharedAccessKey={}".format(
        live_iothub_config['hostname'],
        live_iothub_config['key_name'],
        live_iothub_config['access_key']
    )
    result['policy'] = live_iothub_config['key_name']
    result['primarykey'] = live_iothub_config['access_key']
    result['entity'] = live_iothub_config['hostname']
    return result


def test_iothub_monitor_events(live_iothub_config):
    try:
        import azext_iot.operations.events3._events as events3
        import azext_iot.operations.events3._builders as builders
    except ImportError:
        pytest.skip("Only runs in IoT CLI env.")

    device_ids = {live_iothub_config["device"], True}
    now = datetime.utcnow()
    epoch = datetime.utcfromtimestamp(0)
    enqueued_time = int(1000 * (now - epoch).total_seconds())
    target = _get_iot_conn_str(live_iothub_config)

    eventHubTarget = builders.EventTargetBuilder().build_iot_hub_target(target)
    events3.executor(
        eventHubTarget,
        consumer_group=live_iothub_config['consumer_group'],
        enqueued_time=enqueued_time,
        properties=[],
        timeout=30000,
        device_id=live_iothub_config["device"],
        output='json',
        devices=device_ids
    )

def test_iothub_monitor_feedback(live_iothub_config):
    pytest.skip("Not yet implemented")


def test_iothub_c2d_message_send(live_iothub_config):
    pytest.skip("Not yet implemented")


if __name__ == '__main__':
    try:
        config = {}
        config['hostname'] = os.environ['IOTHUB_HOSTNAME']
        config['hub_name'] = os.environ['IOTHUB_HUB_NAME']
        config['device'] = os.environ['IOTHUB_DEVICE']
        config['endpoint'] = os.environ['IOTHUB_ENDPOINT']
        config['key_name'] = os.environ['IOTHUB_SAS_POLICY']
        config['access_key'] = os.environ['IOTHUB_SAS_KEY']
        config['consumer_group'] = "$Default"
        config['partition'] = "0"
    except KeyError:
        pytest.skip("Live IoTHub configuration not found.")
    else:
        test_iothub_monitor_events(config)