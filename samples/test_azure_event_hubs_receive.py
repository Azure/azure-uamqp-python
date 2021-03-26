#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import os
import pytest
import sys
import time

try:
    from urllib import quote_plus #Py2
except Exception:
    from urllib.parse import quote_plus

import uamqp
from uamqp import address, types, utils, authentication, MessageBodyType
from uamqp.message import DataBody, SequenceBody, ValueBody


def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.INFO)


def get_plain_auth(config):
    return authentication.SASLPlain(
        config['hostname'],
        config['key_name'],
        config['access_key'])


def send_single_message(live_eventhub_config, partition, msg_content):
    target = "amqps://{}/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        partition
    )
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    uamqp.send_message(target, msg_content, auth=sas_auth, debug=False)


def send_multiple_message(live_eventhub_config, msg_count):
    def data_generator():
        for i in range(msg_count):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'], live_eventhub_config['partition'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    message_batch = uamqp.message.BatchMessage(data_generator())
    send_client.queue_message(message_batch)
    results = send_client.send_all_messages(close_on_done=False)
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    send_client.close()


def test_event_hubs_simple_receive(live_eventhub_config):
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    msg_content = b"Hello world"
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    result = uamqp.send_message(target, msg_content, auth=get_plain_auth(live_eventhub_config))

    message = uamqp.receive_message(source, auth=get_plain_auth(live_eventhub_config), timeout=10000)
    assert message
    log.info("Received: {}".format(message.get_data()))


def test_event_hubs_simple_batch_receive(live_eventhub_config):

    source = "amqps://{}:{}@{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        quote_plus(live_eventhub_config['key_name']),
        quote_plus(live_eventhub_config['access_key']),
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    messages = uamqp.receive_messages(source, max_batch_size=10)
    assert len(messages) <= 10

    message = uamqp.receive_messages(source, max_batch_size=1)
    assert len(message) == 1


def test_event_hubs_single_batch_receive(live_eventhub_config):
    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    message = uamqp.receive_messages(source, auth=plain_auth, timeout=5000)
    assert len(message) <= 300


def test_event_hubs_client_web_socket(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'],
        transport_type=uamqp.TransportType.AmqpOverWebsocket)

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    with uamqp.ReceiveClient(source, auth=sas_auth, debug=False, timeout=5000, prefetch=50) as receive_client:
        receive_client.receive_message_batch(max_batch_size=10)


def test_event_hubs_client_proxy_settings(live_eventhub_config):
    pytest.skip("skipping the test in CI due to no proxy server")
    proxy_settings={'proxy_hostname': '127.0.0.1', 'proxy_port': 12345}
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'], http_proxy=proxy_settings)

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    with uamqp.ReceiveClient(source, auth=sas_auth, debug=False, timeout=5000, prefetch=50) as receive_client:
        receive_client.receive_message_batch(max_batch_size=10)


def test_event_hubs_client_receive_sync(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])
    with uamqp.ReceiveClient(source, auth=sas_auth, debug=False, timeout=5000, prefetch=50) as receive_client:
        log.info("Created client, receiving...")
        with pytest.raises(ValueError):
            batch = receive_client.receive_message_batch(max_batch_size=100)
        batch = receive_client.receive_message_batch(max_batch_size=10)
        while batch:
            log.info("Got batch: {}".format(len(batch)))
            assert len(batch) <= 10
            for message in batch:
                annotations = message.annotations
                log.info("Sequence Number: {}, Delivery tag: {}".format(
                    annotations.get(b'x-opt-sequence-number'),
                    message.delivery_tag))
            batch = receive_client.receive_message_batch(max_batch_size=10)
    log.info("Finished receiving")


def test_event_hubs_client_receive_no_shutdown_after_timeout_sync(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    source = address.Source(source)
    source.set_filter(b"amqp.annotation.x-opt-offset > '@latest'")
    received_cnt = 0

    with uamqp.ReceiveClient(source, auth=sas_auth, timeout=2000, debug=False, shutdown_after_timeout=False) as receive_client:
        log.info("Created client, receiving...")

        received_cnt += len(receive_client.receive_message_batch(max_batch_size=10))
        assert received_cnt == 0

        message_handler_before = receive_client.message_handler

        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        received_cnt += len(receive_client.receive_message_batch(max_batch_size=10))
        assert received_cnt == 1

        received_cnt += len(receive_client.receive_message_batch(max_batch_size=10))
        assert received_cnt == 1

        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        received_cnt += len(receive_client.receive_message_batch(max_batch_size=10))
        message_handler_after = receive_client.message_handler

        assert message_handler_before == message_handler_after
        assert received_cnt == 2


def test_event_hubs_client_receive_with_runtime_metric_sync(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receiver_runtime_metric_symbol = b'com.microsoft:enable-receiver-runtime-metric'
    symbol_array = [types.AMQPSymbol(receiver_runtime_metric_symbol)]
    desired_capabilities = utils.data_factory(types.AMQPArray(symbol_array))

    with uamqp.ReceiveClient(source, auth=sas_auth, debug=False, timeout=50, prefetch=50,
                             desired_capabilities=desired_capabilities) as receive_client:
        log.info("Created client, receiving...")
        with pytest.raises(ValueError):
            batch = receive_client.receive_message_batch(max_batch_size=100)
        batch = receive_client.receive_message_batch(max_batch_size=10)
        log.info("Got batch: {}".format(len(batch)))
        assert len(batch) <= 10
        for message in batch:
            annotations = message.annotations
            delivery_annotations = message.delivery_annotations
            log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
            assert b'last_enqueued_sequence_number' in delivery_annotations
            assert b'last_enqueued_offset' in delivery_annotations
            assert b'last_enqueued_time_utc' in delivery_annotations
            assert b'runtime_info_retrieval_time_utc' in delivery_annotations
    log.info("Finished receiving")


def test_event_hubs_callback_receive_sync(live_eventhub_config):

    def on_message_received(message):
        annotations = message.annotations
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info(str(message))
        message.accept()

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=1000, debug=False)
    log.info("Created client, receiving...")
    
    receive_client.receive_messages(on_message_received)
    log.info("Finished receiving")


def test_event_hubs_callback_receive_no_shutdown_after_timeout_sync(live_eventhub_config):
    received_cnt = {'cnt': 0}

    def on_message_received(message):
        annotations = message.annotations
        log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
        log.info(str(message))
        message.accept()
        received_cnt['cnt'] += 1

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])
    
    source = address.Source(source)
    source.set_filter(b"amqp.annotation.x-opt-offset > '@latest'")

    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=2000, debug=False, shutdown_after_timeout=False)
    log.info("Created client, receiving...")
    try:
        receive_client.open()
        while not receive_client.client_ready():
            time.sleep(0.05)

        time.sleep(1)
        receive_client._connection.work()

        assert not receive_client._was_message_received
        assert receive_client._received_messages.empty()

        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        receive_client.receive_messages(on_message_received)
        message_handler_before = receive_client.message_handler
        assert received_cnt['cnt'] == 1

        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        receive_client.receive_messages(on_message_received)
        message_handler_after = receive_client.message_handler
        assert message_handler_before == message_handler_after

        assert received_cnt['cnt'] == 2

        log.info("Finished receiving")
    finally:
        receive_client.close()


def test_event_hubs_iter_receive_sync(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=1000, debug=False, prefetch=10)
    count = 0
    gen = receive_client.receive_messages_iter()
    for message in gen:
        log.info(message.annotations.get(b'x-opt-sequence-number'))
        log.info(str(message))
        count += 1
        if count >= 10:
            log.info("Got {} messages. Breaking.".format(count))
            message.accept()
            break
    count = 0
    for message in gen:
        count += 1
        if count >= 10:
            log.info("Got {} more messages. Shutting down.".format(count))
            message.accept()
            break

    receive_client.close()


def test_event_hubs_iter_receive_no_shutdown_after_timeout_sync(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    source = address.Source(source)
    source.set_filter(b"amqp.annotation.x-opt-offset > '@latest'")
    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=2000, debug=False, shutdown_after_timeout=False)
    count = 0
    try:
        receive_client.open()
        while not receive_client.client_ready():
            time.sleep(0.05)

        time.sleep(1)
        receive_client._connection.work()

        assert not receive_client._was_message_received
        assert receive_client._received_messages.empty()

        gen = receive_client.receive_messages_iter()

        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        for message in gen:
            log.info(message.annotations.get(b'x-opt-sequence-number'))
            log.info(str(message))
            count += 1

        assert count == 1
        count = 0

        message_handler_before = receive_client.message_handler
        send_single_message(live_eventhub_config, live_eventhub_config['partition'], 'message')
        gen = receive_client.receive_messages_iter()

        for message in gen:
            log.info(message.annotations.get(b'x-opt-sequence-number'))
            log.info(str(message))
            count += 1

        assert count == 1

        message_handler_after = receive_client.message_handler
        assert message_handler_before == message_handler_after
    finally:
        receive_client.close()


def test_event_hubs_shared_connection(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'])

    send_single_message(live_eventhub_config, "0", "Message")
    send_single_message(live_eventhub_config, "1", "Message")

    with uamqp.Connection(live_eventhub_config['hostname'], sas_auth, debug=False) as conn:
        partition_0 = uamqp.ReceiveClient(source + "0", debug=False, auth=sas_auth, timeout=3000, prefetch=10)
        partition_1 = uamqp.ReceiveClient(source + "1", debug=False, auth=sas_auth, timeout=3000, prefetch=10)
        partition_0.open(connection=conn)
        partition_1.open(connection=conn)

        try:
            messages_0 = partition_0.receive_message_batch(1)
            messages_1 = partition_1.receive_message_batch(1)
            assert len(messages_0) == 1 and len(messages_1) == 1
        except:
            raise
        finally:
            partition_0.close()
            partition_1.close()


def test_event_hubs_filter_receive(live_eventhub_config):
    plain_auth = authentication.SASLPlain(
        live_eventhub_config['hostname'],
        live_eventhub_config['key_name'],
        live_eventhub_config['access_key'])
    source_url = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])
    source = address.Source(source_url)
    source.set_filter(b"amqp.annotation.x-opt-sequence-number > 1500")

    with uamqp.ReceiveClient(source, auth=plain_auth, timeout=5000, prefetch=50) as receive_client:
        log.info("Created client, receiving...")
        batch = receive_client.receive_message_batch(max_batch_size=10)
        while batch:
            for message in batch:
                annotations = message.annotations
                log.info("Partition Key: {}".format(annotations.get(b'x-opt-partition-key')))
                log.info("Sequence Number: {}".format(annotations.get(b'x-opt-sequence-number')))
                log.info("Offset: {}".format(annotations.get(b'x-opt-offset')))
                log.info("Enqueued Time: {}".format(annotations.get(b'x-opt-enqueued-time')))
                log.info("Message format: {}".format(message._message.message_format))
                log.info("{}".format(list(message.get_data())))
            batch = receive_client.receive_message_batch(max_batch_size=10)
    log.info("Finished receiving")


def test_event_hubs_dynamic_issue_link_credit(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    msg_sent_cnt = 200
    send_multiple_message(live_eventhub_config, msg_sent_cnt)

    def message_received_callback(message):
        message_received_callback.received_msg_cnt += 1

    message_received_callback.received_msg_cnt = 0

    with uamqp.ReceiveClient(source, auth=sas_auth, debug=True, prefetch=1) as receive_client:

        receive_client._message_received_callback = message_received_callback

        while not receive_client.client_ready():
            time.sleep(0.05)

        time.sleep(1)
        receive_client._connection.work()

        assert not receive_client._was_message_received
        assert receive_client._received_messages.empty()

        receive_client.message_handler.reset_link_credit(msg_sent_cnt)

        now = start = time.time()
        wait_time = 5
        while now - start <= wait_time:
            receive_client._connection.work()
            now = time.time()

        assert message_received_callback.received_msg_cnt == msg_sent_cnt
    log.info("Finished receiving")


def test_event_hubs_send_event_with_amqp_attributes_sync(live_eventhub_config):
    def data_generator():
        for i in range(2):
            msg = uamqp.message.Message(body='Data')
            # header is only used on received msg, not set on messages being sent
            msg.application_properties = {'msg_type': 'rich_batch'}
            msg.properties = uamqp.message.MessageProperties(message_id='richid', user_id=b'!@qwe\0?123')
            msg.footer = {'footerkey':'footervalue'}
            msg.delivery_annotations = {'deliveryannkey':'deliveryannvalue'}
            msg.annotations = {'annkey':'annvalue'}
            yield msg

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)

    message = uamqp.message.Message(body='Data')
    # header is only used on received msg, not set on messages being sent
    message.application_properties = {'msg_type': 'rich_single'}
    message.properties = uamqp.message.MessageProperties(message_id='richid')
    message.footer = {'footerkey':'footervalue'}
    message.delivery_annotations = {'deliveryannkey':'deliveryannvalue'}
    message.annotations = {'annkey':'annvalue'}
    send_client.queue_message(message)

    message_batch = uamqp.message.BatchMessage(data_generator())
    send_client.queue_message(message_batch)
    results = send_client.send_all_messages(close_on_done=False)
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]

    rich_single_received = rich_batch_received = False

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        0)

    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=5000, debug=False, prefetch=10)
    gen = receive_client.receive_messages_iter()
    for message in gen:
        if message.application_properties and message.application_properties.get(b'msg_type'):
            if not rich_single_received:
                rich_single_received = message.application_properties.get(b'msg_type') == b'rich_single'
            if not rich_batch_received:
                rich_batch_received = message.application_properties.get(b'msg_type') == b'rich_batch'

            if message.application_properties.get(b'msg_type') == b'rich_single':
                assert message.properties.user_id is None
            elif message.application_properties.get(b'msg_type') == b'rich_batch':
                assert message.properties.user_id == b'!@qwe\0?123'

            assert message.properties.message_id == b'richid'
            assert message.delivery_annotations
            assert message.delivery_annotations.get(b'deliveryannkey') == b'deliveryannvalue'
            assert message.footer
            assert message.footer.get(b'footerkey') == b'footervalue'
            assert message.annotations
            assert message.annotations.get(b'annkey') == b'annvalue'

        log.info(message.annotations.get(b'x-opt-sequence-number'))
        log.info(str(message))

    send_client.close()
    receive_client.close()

    assert rich_single_received
    assert rich_batch_received


def test_event_hubs_not_receive_events_during_connection_establishment(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        live_eventhub_config['partition'])

    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=1000, debug=False, prefetch=10)
    try:
        receive_client.open()

        while not receive_client.client_ready():
            time.sleep(0.05)

        time.sleep(1)  # sleep for 1s
        receive_client._connection.work()  # do a single connection iteration to see if there're incoming transfers

        # make sure no messages are received
        assert not receive_client._was_message_received
        assert receive_client._received_messages.empty()

        messages_0 = receive_client.receive_message_batch()
        assert len(messages_0) > 0
    finally:
        receive_client.close()


def event_hubs_send_different_amqp_body_type_sync(live_eventhub_config):

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)

    data_body_1 = [b'data1', b'data2']
    data_body_message_1 = uamqp.message.Message(body=data_body_1)
    data_body_message_1.application_properties = {'body_type': 'data_body_1'}
    send_client.queue_message(data_body_message_1)

    data_body_2 = b'data1'
    data_body_message_2 = uamqp.message.Message(body=data_body_2, body_type=MessageBodyType.Data)
    data_body_message_2.application_properties = {'body_type': 'data_body_2'}
    send_client.queue_message(data_body_message_2)

    value_body_1 = [b'data1', -1.23, True, {b'key': b'value'}, [1, False, 1.23, b'4']]
    value_body_message_1 = uamqp.message.Message(body=value_body_1)
    value_body_message_1.application_properties = {'body_type': 'value_body_1'}
    send_client.queue_message(value_body_message_1)

    value_body_2 = {b'key1': {b'sub_key': b'sub_value'}, b'key2': b'value', 3: -1.23}
    value_body_message_2 = uamqp.message.Message(body=value_body_2, body_type=MessageBodyType.Value)
    value_body_message_2.application_properties = {'body_type': 'value_body_2'}
    send_client.queue_message(value_body_message_2)

    sequence_body_1 = [b'data1', -1.23, True, {b'key': b'value'}, [b'a', 1.23, True]]
    sequence_body_message_1 = uamqp.message.Message(body=sequence_body_1, body_type=MessageBodyType.Sequence)
    sequence_body_message_1.application_properties = {'body_type': 'sequence_body_1'}
    send_client.queue_message(sequence_body_message_1)

    sequence_body_2 = [[1, 2, 3], [b'aa', b'bb', b'cc'], [True, False, True], [{b'key1': b'value'}, {b'key2': 123}]]
    sequence_body_message_2 = uamqp.message.Message(body=sequence_body_2, body_type=MessageBodyType.Sequence)
    sequence_body_message_2.application_properties = {'body_type': 'sequence_body_2'}
    send_client.queue_message(sequence_body_message_2)

    results = send_client.send_all_messages(close_on_done=False)
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]

    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    source = "amqps://{}/{}/ConsumerGroups/{}/Partitions/{}".format(
        live_eventhub_config['hostname'],
        live_eventhub_config['event_hub'],
        live_eventhub_config['consumer_group'],
        0)

    result_dic = {}
    receive_client = uamqp.ReceiveClient(source, auth=sas_auth, timeout=5000, debug=False, prefetch=10)
    gen = receive_client.receive_messages_iter()
    for message in gen:
        if message.application_properties and message.application_properties.get(b'body_type'):
            if message.application_properties.get(b'body_type') == b'data_body_1':
                check_list = [data for data in message.get_data()]
                assert isinstance(message._body, DataBody)
                assert check_list == data_body_1
                result_dic['data_body_1'] = 1
            elif message.application_properties.get(b'body_type') == b'data_body_2':
                check_list = [data for data in message.get_data()]
                assert isinstance(message._body, DataBody)
                assert check_list == [data_body_2]
                result_dic['data_body_2'] = 1
            elif message.application_properties.get(b'body_type') == b'value_body_1':
                assert message.get_data() == value_body_1
                assert isinstance(message._body, ValueBody)
                result_dic['value_body_1'] = 1
            elif message.application_properties.get(b'body_type') == b'value_body_2':
                assert message.get_data() == value_body_2
                assert isinstance(message._body, ValueBody)
                result_dic['value_body_2'] = 1
            elif message.application_properties.get(b'body_type') == b'sequence_body_1':
                check_list = [data for data in message.get_data()]
                assert check_list == [sequence_body_1]
                assert isinstance(message._body, SequenceBody)
                result_dic['sequence_body_1'] = 1
            elif message.application_properties.get(b'body_type') == b'sequence_body_2':
                check_list = [data for data in message.get_data()]
                assert check_list == sequence_body_2
                assert isinstance(message._body, SequenceBody)
                result_dic['sequence_body_2'] = 1

            log.info(message.annotations.get(b'x-opt-sequence-number'))
            log.info(str(message))

    send_client.close()
    receive_client.close()
    assert len(result_dic) == 6


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"
    event_hubs_send_different_amqp_body_type_sync(config)
