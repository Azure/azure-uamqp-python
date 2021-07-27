# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import asyncio
import json
import sys
import os
import logging
import pytest
from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC
from time import time
from datetime import datetime
from uuid import uuid4
import concurrent

import uamqp


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


DEBUG = True
logger = get_logger(logging.INFO)


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
    hub_name = target['entity'].split('.')[0]
    username = "{}@sas.root.{}".format(target['policy'], hub_name)
    sas_token = _generate_sas_token(target['entity'], target['policy'],
                                    target['primarykey'], time() + 360)
    return username, sas_token


def _unicode_binary_map(target):
    # Assumes no iteritems()
    result = {}
    for k in target:
        key = k
        if isinstance(k, bytes):
            key = str(k, 'utf8')
        if isinstance(target[k], bytes):
            result[key] = str(target[k], 'utf8')
        else:
            result[key] = target[k]
    return result


def _parse_entity(entity, filter_none=False):
    result = {}
    attributes = [attr for attr in dir(entity) if not attr.startswith('_')]
    for attribute in attributes:
        value = getattr(entity, attribute, None)
        if filter_none and not value:
            continue
        value_behavior = dir(value)
        if '__call__' not in value_behavior:
            result[attribute] = value
    return result


def executor(target, consumer_group, enqueued_time, device_id=None, properties=None, timeout=0):
    coroutines = []
    coroutines.append(initiate_event_monitor(target, consumer_group, enqueued_time, device_id, properties, timeout))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    future = asyncio.gather(*coroutines, return_exceptions=True)
    result = None

    try:
        device_filter_txt = None
        if device_id:
            device_filter_txt = ' filtering on device: {},'.format(device_id)

        def stop_and_suppress_eloop():
            try:
                loop.stop()
            except Exception:  # pylint: disable=broad-except
                pass

        print('Starting event monitor,{} use ctrl-c to stop...'.format(device_filter_txt if device_filter_txt else ''))
        result = loop.run_until_complete(future)
    except KeyboardInterrupt:
        print('Stopping event monitor...')
        remaining_tasks = [t for t in asyncio.Task.all_tasks() if not t.done()]
        remaining_future = asyncio.gather(*remaining_tasks, return_exceptions=True)
        try:
            loop.run_until_complete(asyncio.wait_for(remaining_future, 5))
        except concurrent.futures.TimeoutError:
            print("Timed out before tasks could finish. Shutting down anyway.")
        print("Finished event monitor shutdown.")
    finally:
        if result:
            error = next(res for res in result if result)
            if error:
                logger.error(error)
                raise RuntimeError(error)


async def initiate_event_monitor(target, consumer_group, enqueued_time, device_id=None, properties=None, timeout=0):
    def _get_conn_props():
        properties = {}
        properties["product"] = "az.cli.iot.extension"
        properties["framework"] = "Python {}.{}.{}".format(*sys.version_info[0:3])
        properties["platform"] = sys.platform
        return properties

    if not target.get('events'):
        endpoint = _build_iothub_amqp_endpoint_from_target(target)
        _, update = await evaluate_redirect(endpoint)
        target['events'] = update['events']
        auth = _build_auth_container(target)
        meta_data = await query_meta_data(target['events']['address'], target['events']['path'], auth)
        partition_count = meta_data[b'partition_count']
        partition_ids = []
        for i in range(int(partition_count)):
            partition_ids.append(str(i))
        target['events']['partition_ids'] = partition_ids

    partitions = target['events']['partition_ids']

    if not partitions:
        logger.debug('No Event Hub partitions found to listen on.')
        return

    coroutines = []
    auth = _build_auth_container(target)
    async with uamqp.ConnectionAsync(target['events']['endpoint'], sasl=auth,
                                        debug=DEBUG, container_id=str(uuid4()), properties=_get_conn_props()) as conn:
        for p in partitions:
            coroutines.append(monitor_events(endpoint=target['events']['endpoint'],
                                            connection=conn,
                                            path=target['events']['path'],
                                            auth=auth,
                                            partition=p,
                                            consumer_group=consumer_group,
                                            enqueuedtimeutc=enqueued_time,
                                            properties=properties,
                                            device_id=device_id,
                                            timeout=timeout))
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        logger.warning("Finished all event monitors")
    logger.warning("Finished initiate_event_monitor")


async def monitor_events(endpoint, connection, path, auth, partition, consumer_group, enqueuedtimeutc,
                         properties, device_id=None, timeout=0):
    source = uamqp.address.Source('amqps://{}/{}/ConsumerGroups/{}/Partitions/{}'.format(endpoint, path,
                                                                                         consumer_group, partition))
    source.set_filter(
        bytes('amqp.annotation.x-opt-enqueuedtimeutc > ' + str(enqueuedtimeutc), 'utf8'))

    def _output_msg_kpi(msg):
        # TODO: Determine if amqp filters can support boolean operators for multiple conditions
        origin = str(msg.annotations.get(b'iothub-connection-device-id'), 'utf8')
        if device_id and origin != device_id:
            return

        event_source = {'event': {}}

        event_source['event']['origin'] = origin
        event_source['event']['payload'] = str(next(msg.get_data()), 'utf8')
        if 'anno' in properties or 'all' in properties:
            event_source['event']['annotations'] = _unicode_binary_map(msg.annotations)
        if 'sys' in properties or 'all' in properties:
            if not event_source['event'].get('properties'):
                event_source['event']['properties'] = {}
            event_source['event']['properties']['system'] = _unicode_binary_map(_parse_entity(msg.properties, True))
        if 'app' in properties or 'all' in properties:
            if not event_source['event'].get('properties'):
                event_source['event']['properties'] = {}
            app_prop = msg.application_properties if msg.application_properties else None

            if app_prop:
                event_source['event']['properties']['application'] = _unicode_binary_map(app_prop)

    exp_cancelled = False
    receive_client = uamqp.ReceiveClientAsync(source, auth=auth, timeout=timeout, prefetch=0, debug=DEBUG)

    try:
        await receive_client.open_async(connection=connection)

        msg_iter = receive_client.receive_messages_iter_async()
        async for msg in msg_iter:
            _output_msg_kpi(msg)

    except asyncio.CancelledError:
        exp_cancelled = True
        await receive_client.close_async()
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt, closing monitor {}.".format(partition))
        exp_cancelled = True
        await receive_client.close_async()
        raise
    except uamqp.errors.LinkDetach as ld:
        if isinstance(ld.description, bytes):
            ld.description = str(ld.description, 'utf8')
        raise RuntimeError(ld.description)
    finally:
        if not exp_cancelled:
            await receive_client.close_async()
        logger.warning("Finished MonitorEvents for partition {}".format(partition))


def _build_auth_container(target):
    sas_uri = 'sb://{}/{}'.format(target['events']['endpoint'], target['events']['path'])
    return uamqp.authentication.SASTokenAsync.from_shared_access_key(sas_uri, target['policy'], target['primarykey'])


async def evaluate_redirect(endpoint):
    source = uamqp.address.Source('amqps://{}/messages/events/$management'.format(endpoint))
    receive_client = uamqp.ReceiveClientAsync(source, timeout=30000, prefetch=1, debug=DEBUG)

    try:
        await receive_client.open_async()
        await receive_client.receive_message_batch_async(max_batch_size=1)
    except uamqp.errors.LinkRedirect as redirect:
        redirect = _unicode_binary_map(_parse_entity(redirect))
        result = {}
        result['events'] = {}
        result['events']['endpoint'] = redirect['hostname']
        result['events']['path'] = redirect['address'].replace('amqps://', '').split('/')[1]
        result['events']['address'] = redirect['address']
        return redirect, result
    finally:
        await receive_client.close_async()


async def query_meta_data(endpoint, path, auth):
    source = uamqp.address.Source(endpoint)
    receive_client = uamqp.ReceiveClientAsync(source, auth=auth, timeout=30000, debug=DEBUG)
    try:
        await receive_client.open_async()
        message = uamqp.Message(application_properties={'name': path})

        response = await receive_client.mgmt_request_async(
            message,
            b'READ',
            op_type=b'com.microsoft:eventhub',
            status_code_field=b'status-code',
            description_fields=b'status-description',
            timeout=30000
        )
        test = response.get_data()
        return test
    finally:
        await receive_client.close_async()


def monitor_feedback(target, device_id, wait_on_id=None, token_duration=3600):

    def handle_msg(msg):
        payload = next(msg.get_data())
        if isinstance(payload, bytes):
            payload = str(payload, 'utf8')
        # assume json [] based on spec
        payload = json.loads(payload)
        for p in payload:
            if device_id and p.get('deviceId') and p['deviceId'].lower() != device_id.lower():
                return None
            if wait_on_id:
                msg_id = p['originalMessageId']
                if msg_id == wait_on_id:
                    return msg_id
        return None

    operation = '/messages/servicebound/feedback'
    endpoint = _build_iothub_amqp_endpoint_from_target(target, duration=token_duration)
    endpoint = endpoint + operation

    device_filter_txt = None
    if device_id:
        device_filter_txt = ' filtering on device: {},'.format(device_id)

    print('Starting C2D feedback monitor,{} use ctrl-c to stop...'.format(device_filter_txt if device_filter_txt else ''))

    try:
        client = uamqp.ReceiveClient('amqps://' + endpoint, debug=DEBUG)
        message_generator = client.receive_messages_iter()
        for msg in message_generator:
            match = handle_msg(msg)
            if match:
                logger.info('requested msg id has been matched...')
                msg.accept()
                return match
    except uamqp.errors.AMQPConnectionError:
        logger.debug('amqp connection has expired...')
    finally:
        client.close()

def get_target(config):
    target = {}
    target['cs'] = 'HostName={};SharedAccessKeyName={};SharedAccessKey={}'.format(
        config['hostname'],
        config['key_name'],
        config['access_key'])
    target['entity'] = config['hostname']
    target['policy'] = config['key_name']
    target['primarykey'] = config['access_key']
    events = {}
    events['endpoint'] = config['endpoint']
    events['partition_count'] = config.get('partition_count', 4)
    events['path'] = config['hub_name']
    events['partition_ids'] = config.get('partition_ids', ["0", "1", "2"])#, "3", "4", "5", "6", "7", "8", "9", "10"])
    target['events'] = events
    return target

def test_iothub_monitor_events(live_iothub_config):
    properties = []
    timeout = 30000
    now = datetime.utcnow()
    epoch = datetime.utcfromtimestamp(0)
    enqueued_time = int(1000 * (now - epoch).total_seconds())
    target = get_target(live_iothub_config)

    executor(target,
             consumer_group=live_iothub_config['consumer_group'],
             enqueued_time=enqueued_time,
             properties=properties,
             timeout=timeout,
             device_id=live_iothub_config['device'])


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