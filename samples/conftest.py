#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import pytest
import sys


# Ignore async tests for Python < 3.5
collect_ignore = []
if sys.version_info < (3, 5):
    collect_ignore.append("asynctests")


@pytest.fixture()
def live_eventhub_config():
    try:
        config = {}
        config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
        config['event_hub'] = os.environ['EVENT_HUB_NAME']
        config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
        config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
        config['consumer_group'] = "$Default"
        config['partition'] = "0"
    except KeyError:
        pytest.skip("Live EventHub configuration not found.")
    else:
        if not all(config.values()):
            pytest.skip("Live EventHub configuration empty.")
        return config


@pytest.fixture()
def live_iothub_config():
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
        if not all(config.values()):
            pytest.skip("Live IoTHub configuration empty.")
        return config


@pytest.fixture()
def rabbit_mq_config():
    try:
        config = {}
        config['hostname'] = os.environ['RABBITMQ_HOSTNAME']
        config['path'] = os.environ['RABBITMQ_PATH']
    except KeyError:
        pytest.skip("Live RabbitMQ configuration not found.")
    else:
        return config

