#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import time
import sys
import uuid
import warnings
import pytest
import datetime

from azure.identity import EnvironmentCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.eventhub import EventHubManagementClient
from uamqp import SendClient, ReceiveClient
from uamqp.authentication import SASLPlainAuth, SASTokenAuth


# Ignore async tests for Python < 3.5
collect_ignore = []
if sys.version_info < (3, 5):
    collect_ignore.append("asynctests")
PARTITION_COUNT = 2
CONN_STR = "Endpoint=sb://{}/;SharedAccessKeyName={};SharedAccessKey={};EntityPath={}"
RES_GROUP_PREFIX = "eh-res-group"
NAMESPACE_PREFIX = "eh-ns"
EVENTHUB_PREFIX = "eh"
EVENTHUB_DEFAULT_AUTH_RULE_NAME = 'RootManageSharedAccessKey'
LOCATION = os.environ.get("RESOURCE_REGION", None) or "westus"

@pytest.fixture(scope="session")
def resource_group():
    try:
        SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
    except KeyError:
        pytest.skip('AZURE_SUBSCRIPTION_ID undefined')
        return
    resource_client = ResourceManagementClient(EnvironmentCredential(), SUBSCRIPTION_ID)
    resource_group_name = RES_GROUP_PREFIX + str(uuid.uuid4())
    parameters = {"location": LOCATION}
    expiry = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    parameters['tags'] = {'DeleteAfter': expiry.replace(microsecond=0).isoformat()}
    try:
        rg = resource_client.resource_groups.create_or_update(
            resource_group_name,
            parameters
        )
        yield rg
    finally:
        try:
            resource_client.resource_groups.begin_delete(resource_group_name)
        except:
            warnings.warn(UserWarning("resource group teardown failed"))


@pytest.fixture(scope="session")
def eventhub_namespace(resource_group):
    try:
        SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
    except KeyError:
        pytest.skip('AZURE_SUBSCRIPTION_ID defined')
        return
    resource_client = EventHubManagementClient(EnvironmentCredential(), SUBSCRIPTION_ID)
    namespace_name = NAMESPACE_PREFIX + str(uuid.uuid4())
    try:
        namespace = resource_client.namespaces.begin_create_or_update(
            resource_group.name, namespace_name, {"location": LOCATION}
        ).result()
        key = resource_client.namespaces.list_keys(resource_group.name, namespace_name, EVENTHUB_DEFAULT_AUTH_RULE_NAME)
        connection_string = key.primary_connection_string
        key_name = key.key_name
        primary_key = key.primary_key
        yield namespace.name, connection_string, key_name, primary_key
    finally:
        try:
            resource_client.namespaces.begin_delete(resource_group.name, namespace_name).wait()
        except:
            warnings.warn(UserWarning("eventhub namespace teardown failed"))

@pytest.fixture()
def eventhub_config():
    try:
        config = {}
        config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
        config['event_hub'] = os.environ['EVENT_HUB_NAME']
        config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
        config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
        config['consumer_group'] = "$Default"
        config['partition'] = "0"
        yield config
    except KeyError:
        pytest.skip("Live EventHub configuration not found.")

@pytest.fixture()
def live_eventhub_config(resource_group, eventhub_namespace):  # pylint: disable=redefined-outer-name
    try:
        SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
    except KeyError:
        pytest.skip('AZURE_SUBSCRIPTION_ID defined')
        return
    resource_client = EventHubManagementClient(EnvironmentCredential(), SUBSCRIPTION_ID)
    eventhub_name = EVENTHUB_PREFIX + str(uuid.uuid4())
    eventhub_ns_name, connection_string, key_name, primary_key = eventhub_namespace
    try:
        eventhub = resource_client.event_hubs.create_or_update(
            resource_group.name, eventhub_ns_name, eventhub_name, {"partition_count": PARTITION_COUNT}
        )
        live_eventhub_config = {
            'resource_group': resource_group.name,
            'hostname': "{}.servicebus.windows.net".format(eventhub_ns_name),
            'key_name': key_name,
            'access_key': primary_key,
            'namespace': eventhub_ns_name,
            'event_hub': eventhub.name,
            'consumer_group': '$Default',
            'partition': '0',
            'connection_str': connection_string + ";EntityPath="+eventhub.name
        }
        yield live_eventhub_config
    finally:
        try:
            resource_client.event_hubs.delete(resource_group.name, eventhub_ns_name, eventhub_name)
        except:
            warnings.warn(UserWarning("eventhub teardown failed"))

@pytest.fixture()
def live_eventhub_send_client(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    target = "amqps://{}/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['partition']
    )
    auth = SASLPlainAuth(
        authcid=live_eventhub_config['key_name'],
        passwd=live_eventhub_config['access_key']
    )
    send_client = SendClient(hostname, target, auth, idle_timeout=10, network_trace=True)
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    yield send_client
    send_client.close()

@pytest.fixture()
def live_eventhub_receive_client(live_eventhub_config):
    hostname = live_eventhub_config['hostname']
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition']
    )
    sas_auth = SASTokenAuth(
        uri=uri,
        audience=uri,
        username=live_eventhub_config['key_name'],
        password=live_eventhub_config['access_key']
    )
    receive_client = ReceiveClient(hostname, source, auth=sas_auth, idle_timeout=10, network_trace=True)
    receive_client.open()
    while not receive_client.client_ready():
        time.sleep(0.05)
    yield receive_client
    receive_client.close()

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

# Note: This is duplicated between here and the basic conftest, so that it does not throw warnings if you're
# running locally to this SDK. (Everything works properly, pytest just makes a bit of noise.)
def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "liveTest: mark test to be a live test only"
    )
