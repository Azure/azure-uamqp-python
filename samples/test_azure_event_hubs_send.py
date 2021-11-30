#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import logging
import sys
import time
from datetime import timedelta
import types
import pytest
import collections

import uamqp
from uamqp import types as uamqp_types, utils, authentication, constants

_AccessToken = collections.namedtuple("AccessToken", "token expires_on")

def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.INFO)


def test_event_hubs_simple_send(live_eventhub_config):
    msg_content = b"Hello world"
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'],live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    result = uamqp.send_message(target, msg_content, auth=sas_auth, debug=False)
    assert result == [uamqp.constants.MessageState.SendComplete]


def test_event_hubs_client_send_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        header = uamqp.message.MessageHeader()
        header.durable = True
        assert header.get_header_obj()
        props = uamqp.message.MessageProperties(message_id=b"message id", subject="test_subject")
        assert props.get_properties_obj()
        msg_content = b"hello world"
        message = uamqp.Message(
            msg_content,
            properties=props,
            header=header,
            application_properties=annotations,
            annotations=annotations)
        assert message.get_message_encoded_size() == 151
        assert message.encode_message() == b'\x00Sp\xc0\x06\x05A@@@C\x00Sr\xc1(\x02\xa1\x13x-opt-partition-key\xa1\x10PartitionKeyInfo\x00Ss\xc0\x1d\x04\xa1\nmessage id@@\xa1\x0ctest_subject\x00St\xc1(\x02\xa1\x13x-opt-partition-key\xa1\x10PartitionKeyInfo\x00Su\xa0\x0bhello world'
        send_client.queue_message(message)
    results = send_client.send_all_messages(close_on_done=False)
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    send_client.close()

def test_event_hubs_client_send_multiple_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])
    assert not sas_auth.consumed

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    messages = []
    for _ in range(10):
        header = uamqp.message.MessageHeader()
        header.durable = True
        header.delivery_count = 5
        header.time_to_live = 500000
        header.first_acquirer = True
        header.priority = 3
        assert header.get_header_obj()
        props = uamqp.message.MessageProperties(
            message_id=b"message id",
            user_id="user_id",
            to="to",
            subject="test",
            reply_to="reply_to",
            correlation_id="correlation_id",
            content_type="content_type",
            content_encoding="content_encoding",
            creation_time=12345,
            absolute_expiry_time=12345,
            group_id="group_id",
            group_sequence=1234,
            reply_to_group_id="reply_to_group_id")
        assert props.get_properties_obj()
        msg_content = b"hello world"
        message = uamqp.Message(
            msg_content,
            properties=props,
            header=header,
            application_properties=annotations,
            annotations=annotations)
        messages.append(message)
    send_client.queue_message(*messages)
    assert len(send_client.pending_messages) == 10
    results = send_client.send_all_messages()
    assert len(results) == 10
    assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    assert sas_auth.consumed
    assert send_client.pending_messages == []


def test_event_hubs_single_send_sync(live_eventhub_config):
    annotations={b"x-opt-partition-key": b"PartitionKeyInfo"}
    msg_content = b"hello world"

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        message = uamqp.Message(msg_content, application_properties=annotations, annotations=annotations)
        send_client.send_message(message)
    send_client.close()


def test_event_hubs_batch_send_sync(live_eventhub_config):
    def data_generator():
        for i in range(50):
            msg_content = "Hello world {}".format(i).encode('utf-8')
            yield msg_content

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False)
    for _ in range(10):
        message_batch = uamqp.message.BatchMessage(data_generator())
        send_client.queue_message(message_batch)
        results = send_client.send_all_messages(close_on_done=False)
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
    send_client.close()


def test_event_hubs_send_timeout_sync(live_eventhub_config):

    def _hack_client_run(cls):
        """MessageSender Link is now open - perform message send
        on all pending messages.
        Will return True if operation successful and client can remain open for
        further work.

        :rtype: bool
        """
        # pylint: disable=protected-access
        time.sleep(6)
        cls.message_handler.work()
        cls._waiting_messages = 0
        cls._pending_messages = cls._filter_pending()
        if cls._backoff and not cls._waiting_messages:
            log.info("Client told to backoff - sleeping for %r seconds", cls._backoff)
            cls._connection.sleep(cls._backoff)
            cls._backoff = 0
        cls._connection.work()
        return True

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=False, msg_timeout=5000)
    send_client._client_run = types.MethodType(_hack_client_run, send_client)
    send_client.open()
    with pytest.raises(uamqp.errors.ClientMessageError):
        send_client.send_message(uamqp.message.Message(body='Hello World'))
    send_client.close()


def test_event_hubs_custom_end_point():
    sas_token = authentication.SASTokenAuth("fake_audience", "fake_uri", "fake_token", expires_in=timedelta(10), custom_endpoint_hostname="123.45.67.89")
    assert sas_token.hostname == b"123.45.67.89"

    sas_token = authentication.SASTokenAuth.from_shared_access_key("fake_uri", "fake_key_name", "fake_key", custom_endpoint_hostname="123.45.67.89")
    assert sas_token.hostname == b"123.45.67.89"

    def fake_get_token():
        return "fake get token"

    jwt_token = authentication.JWTTokenAuth("fake_audience", "fake_uri", fake_get_token, custom_endpoint_hostname="123.45.67.89")
    assert jwt_token.hostname == b"123.45.67.89"


def test_event_hubs_idempotent_producer(live_eventhub_config):

    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])

    symbol_array = [uamqp_types.AMQPSymbol(b"com.microsoft:idempotent-producer")]
    desired_capabilities = utils.data_factory(uamqp_types.AMQPArray(symbol_array))

    link_properties = {
        uamqp_types.AMQPSymbol(b"com.microsoft:timeout"): uamqp_types.AMQPLong(int(60 * 1000))
    }

    def on_attach(attach_source, attach_target, properties, error):
        if str(attach_target) == target:
            on_attach.owner_level = properties.get(b"com.microsoft:producer-epoch")
            on_attach.producer_group_id = properties.get(b"com.microsoft:producer-id")
            on_attach.starting_sequence_number = properties.get(b"com.microsoft:producer-sequence-number")

    send_client = uamqp.SendClient(
        target,
        auth=sas_auth,
        desired_capabilities=desired_capabilities,
        link_properties=link_properties,
        on_attach=on_attach,
        debug=True
    )
    send_client.open()
    while not send_client.client_ready():
        time.sleep(0.05)
    assert on_attach.owner_level is not None
    assert on_attach.producer_group_id is not None
    assert on_attach.starting_sequence_number is not None
    send_client.close()


def test_event_hubs_send_large_message_after_socket_lost(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    sas_auth = authentication.SASTokenAuth.from_shared_access_key(
        uri, live_eventhub_config['key_name'], live_eventhub_config['access_key'])

    target = "amqps://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    send_client = uamqp.SendClient(target, auth=sas_auth, debug=True)
    try:
        send_client.open()
        while not send_client.client_ready():
            send_client.do_work()
        # the connection idle timeout setting on the EH service is 240s, after 240s no activity
        # on the connection, the service would send detach to the client, the underlying socket on the client
        # is still able to work to receive the frame.
        # HOWEVER, after no activity on the client socket > 300s, the underlying socket would get completely lost:
        # the socket reports "Failure: sending socket failed 10054" on windows
        # or "Failure: sending socket failed. errno=104" on linux which indicates the socket is lost
        time.sleep(350)

        with pytest.raises(uamqp.errors.AMQPConnectionError):
            send_client.send_message(uamqp.message.Message(b't'*1024*700))
    finally:
        send_client.close()


def test_event_hubs_send_override_token_refresh_window(live_eventhub_config):
    uri = "sb://{}/{}".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    target = "amqps://{}/{}/Partitions/0".format(live_eventhub_config['hostname'], live_eventhub_config['event_hub'])
    token = [None]

    def get_token():
        return _AccessToken(token[0], expiry)

    jwt_auth = authentication.JWTTokenAuth(
        uri,
        uri,
        get_token,
        refresh_window=300  # set refresh window to be 5 mins
    )

    send_client = uamqp.SendClient(target, auth=jwt_auth, debug=False)

    # use token of which the valid remaining time < refresh window
    expiry = int(time.time()) + (60 * 4 + 30)  # 4.5 minutes
    token[0] = utils.create_sas_token(
        live_eventhub_config['key_name'].encode(),
        live_eventhub_config['access_key'].encode(),
        uri.encode(),
        expiry=timedelta(minutes=4, seconds=30)
    )

    for _ in range(3):
        message = uamqp.message.Message(body='Hello World')
        send_client.send_message(message)

    auth_status = constants.CBSAuthStatus(jwt_auth._cbs_auth.get_status())
    assert auth_status == constants.CBSAuthStatus.RefreshRequired

    # update token, the valid remaining time > refresh window
    expiry = int(time.time()) + (60 * 5 + 30)  # 5.5 minutes
    token[0] = utils.create_sas_token(
        live_eventhub_config['key_name'].encode(),
        live_eventhub_config['access_key'].encode(),
        uri.encode(),
        expiry=timedelta(minutes=5, seconds=30)
    )

    for _ in range(3):
        message = uamqp.message.Message(body='Hello World')
        send_client.send_message(message)

    auth_status = constants.CBSAuthStatus(jwt_auth._cbs_auth.get_status())
    assert auth_status == constants.CBSAuthStatus.Ok
    send_client.close()


if __name__ == '__main__':
    config = {}
    config['hostname'] = os.environ['EVENT_HUB_HOSTNAME']
    config['event_hub'] = os.environ['EVENT_HUB_NAME']
    config['key_name'] = os.environ['EVENT_HUB_SAS_POLICY']
    config['access_key'] = os.environ['EVENT_HUB_SAS_KEY']
    config['consumer_group'] = "$Default"
    config['partition'] = "0"

    test_event_hubs_send_override_token_refresh_window(config)
