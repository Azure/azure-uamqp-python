


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

def main():
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    c = Connection(
        "amqps://" + config['hostname'],
        transport=SASLTransport(config['hostname'], creds, ssl={'ca_certs':certifi.where()}),
        max_frame_size=65536,
        channel_max=65535,
        idle_timeout=10)

    c.open()
    session = c.begin_session(
        incoming_window=500,
        outgoing_window=500)
    session2 = c.begin_session()

    target = Target(address="amqps://{}/{}/Partitions/0".format(config['hostname'], config['event_hub']))
    link = session.attach_sender_link(
        target=target,
        send_settle_mode='UNSETTLED',
        rcv_settle_mode='SECOND'
    )
    c.listen()
    for i in range(2):
        message = BareMessage(data=b'HelloFromPython')
        link.send_transfer(message, on_send_complete=message_send_complete, timeout=2)
    time.sleep(2)
    c.listen(timeout=2)
    c.listen(timeout=2)
    c.listen(timeout=3)
    session.detach_link(link, close=True)
    c.listen()
    source = Source(address="amqps://{}/{}/ConsumerGroups/$Default/Partitions/0".format(
        config['hostname'],
        config['event_hub']))
    print("ATTACHING RECEIVER")
    link = session.attach_receiver_link(
        source=source,
        send_settle_mode='UNSETTLED',
        rcv_settle_mode='SECOND',
        max_message_size=1048576,
    )
    while True:
        c.listen(timeout=2)
    print("DETACHING RECEIVER")
    session.detach_link(link, close=True)
    c.listen()
    print("ENDING SESSION")
    c.end_session(session)
    c.end_session(session2)
    print("CLOSING")
    c.close()

if __name__ == '__main__':
    main()