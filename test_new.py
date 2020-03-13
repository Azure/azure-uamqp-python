


import certifi
import ssl
import os
import logging
import sys
import time

from uamqp import Connection
from uamqp.sasl import SASLTransport, SASLAnonymousCredential, SASLPlainCredential
from uamqp.endpoints import Source, Target
from uamqp.message import BareMessage

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

def message_send_complete(message, reason, state):
    print("MESSAGE SEND COMPLETE", reason, state)

def message_received(message):
    #print("MESSAGE RECEIVED", message['data'])
    pass

def main():
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    with Connection(
        "amqps://" + config['hostname'],
        transport=SASLTransport(config['hostname'], creds, ssl={'ca_certs':certifi.where()}),
        max_frame_size=65536,
        channel_max=65535,
        idle_timeout=10) as c:

        with c.create_session(
            incoming_window=500,
            outgoing_window=500) as session:

            target = Target(address="amqps://{}/{}/Partitions/0".format(config['hostname'], config['event_hub']))
            with session.create_sender_link(
                target=target,
                send_settle_mode='UNSETTLED',
                rcv_settle_mode='SECOND'
            ) as link:
                while link.state.value != 3: #'ATTACHED':
                    print(link.state.value)
                    c.listen()
                for i in range(2):
                    message = BareMessage(data=b'HelloFromPython')
                    link.send_transfer(message, on_send_complete=message_send_complete, timeout=2)
                c.listen(wait=2)
                c.listen(wait=2)
                c.listen(wait=2)

            c.listen()

            source = Source(address="amqps://{}/{}/ConsumerGroups/$Default/Partitions/0".format(
                config['hostname'],
                config['event_hub']))
            print("ATTACHING RECEIVER")
            with session.create_receiver_link(
                source=source,
                send_settle_mode='UNSETTLED',
                rcv_settle_mode='SECOND',
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