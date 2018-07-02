#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import pytest


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
        return config


@pytest.fixture()
def live_iothub_config():
    try:
        config = {}
        config['hostname'] = os.environ['IOTHUB_HOSTNAME']
        config['device'] = os.environ['IOTHUB_DEVICE']
        config['key_name'] = os.environ['IOTHUB_SAS_POLICY']
        config['access_key'] = os.environ['IOTHUB_SAS_KEY']
        config['consumer_group'] = "$Default"
        config['partition'] = "0"
    except KeyError:
        pytest.skip("Live IoTHub configuration not found.")
    else:
        return config

