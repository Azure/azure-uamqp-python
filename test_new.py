


import certifi
import ssl
import os

from uamqp import Connection
from uamqp.sasl import SASLTransport, SASLAnonymousCredential, SASLPlainCredential
from uamqp.endpoints import Source, Target

from legacy_test.live_settings import config


def main():
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    c = Connection(
        "amqps://" + config['hostname'],
        transport=SASLTransport(config['hostname'], creds, ssl={'ca_certs':certifi.where()}),
        max_frame_size=65536,
        channel_max=65535)

    c.connect()
    c.open()
    c.do_work()
    session = c.begin_session()
    c.do_work()
    session2 = c.begin_session()
    c.do_work()

    target = Target(address="amqps://{}/{}".format(config['hostname'], config['event_hub']))
    link = session.attach_sender_link(
        target=target,
        send_settle_mode='SETTLED',
        rcv_settle_mode='SECOND'
    )
    c.do_work()
    session.detach_link(link)
    c.do_work()
    c.end_session(session)
    c.do_work()
    c.end_session(session2)
    c.do_work()
    c.close()
    c.do_work()
    c.disconnect()

if __name__ == '__main__':
    main()