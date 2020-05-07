


import certifi
import ssl
import os
import logging
import sys
import time
import functools
from collections import namedtuple

from uamqp import Connection
from uamqp.sasl import SASLTransport, SASLAnonymousCredential, SASLPlainCredential
from uamqp.endpoints import Source, Target
from uamqp.message import Message
from uamqp.constants import SenderSettleMode, ReceiverSettleMode
from uamqp.cbs import CbsAuth
from uamqp.utils import generate_sas_token

from legacy_test.live_settings import config

def get_logger(level):
    uamqp_logger = logging.getLogger("uamqp")
    if not uamqp_logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        uamqp_logger.addHandler(handler)
    uamqp_logger.setLevel(level)
    return uamqp_logger


log = get_logger(logging.DEBUG)

AccessToken = namedtuple("AccessToken", ['token', 'expires_on'])


def generate_token(auth_audience, key_name, access_key, duration):
    abs_exipry = int(time.time() + duration)
    token = generate_sas_token(auth_audience, key_name, access_key, abs_exipry)
    return AccessToken(token, abs_exipry)


def message_send_complete(message, reason, state):
    print("MESSAGE SEND COMPLETE", reason, state)


def message_received(message):
    print("MESSAGE RECEIVED", message['data'])


def main():
    creds = SASLAnonymousCredential()
    with Connection(
        "amqps://" + config['hostname'],
        transport=SASLTransport(config['hostname'], creds, ssl={'ca_certs':certifi.where()}),
        network_trace=True,
        max_frame_size=65536,
        channel_max=65535,
        idle_timeout=20) as c:
        c.listen()
        with c.create_session(
            incoming_window=500,
            outgoing_window=500) as session:
            c.listen()
            target = "amqps://{}/{}/Partitions/0".format(config['hostname'], config['event_hub'])

            auth_audience = "sb://{}/{}".format(config['hostname'], config['event_hub'])
            get_token = functools.partial(generate_token, auth_audience, config['key_name'], config['access_key'], 3600)
            cbs = CbsAuth(
                session=session,
                auth_audience=auth_audience,
                get_token=get_token
            )

            cbs.open()
            while cbs.state.value != 2:  # OPEN
                c.listen()

            cbs.handle_token()

            while cbs.auth_state.value != 0:  # OK
                c.listen()

            with session.create_sender_link(
                target_address=target,
                send_settle_mode=SenderSettleMode.Unsettled,
                rcv_settle_mode=ReceiverSettleMode.Second
            ) as link:
                while link.state.value != 3: #'ATTACHED':
                    print(link.state.value)
                    c.listen()
                for i in range(2):
                    message = Message(data=b'HelloFromPython')
                    link.send_transfer(message, on_send_complete=message_send_complete, timeout=2)
                c.listen(wait=2)
                c.listen(wait=2)
                c.listen(wait=2)

            c.listen()

            source = "amqps://{}/{}/ConsumerGroups/$Default/Partitions/0".format(config['hostname'], config['event_hub'])
            print("ATTACHING RECEIVER")
            with session.create_receiver_link(
                source_address=source,
                send_settle_mode=SenderSettleMode.Unsettled,
                rcv_settle_mode=ReceiverSettleMode.Second,
                max_message_size=1048576,
                on_message_received=message_received,
            ) as link:

                for _ in range(10):
                    print("LISTENING")
                    c.listen()
                print("DETACHING RECEIVER")
            c.listen()
            print("ENDING SESSION")
        print("CLOSING")
    print("DONE")

if __name__ == '__main__':
    main()