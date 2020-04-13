

import asyncio
import certifi
import ssl
import os
import logging
import sys
import time

from uamqp.aio import Connection
from uamqp.aio import SASLTransport, SASLPlainCredential
from uamqp.endpoints import Source, Target
from uamqp.message import Message
from uamqp.constants import SenderSettleMode, ReceiverSettleMode

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

async def message_send_complete(message, reason, state):
    print("MESSAGE SEND COMPLETE", reason, state)

async def message_received(message):
    print("MESSAGE RECEIVED", message['data'])

async def main():
    creds = SASLPlainCredential(authcid=config['key_name'], passwd=config['access_key'])
    async with Connection(
            "amqps://" + config['hostname'],
            #transport=SASLTransport(config['hostname'], creds, ssl={'ca_certs':certifi.where()}),
            transport=SASLTransport(config['hostname'], creds, ssl={'context':{}}),
            network_trace=True,
            max_frame_size=65536,
            channel_max=65535,
            idle_timeout=10) as c:
        await c.listen()
        async with c.create_session(
            incoming_window=500,
            outgoing_window=500) as session:
            await c.listen()
            target = "amqps://{}/{}/Partitions/0".format(config['hostname'], config['event_hub'])
            async with session.create_sender_link(
                target_address=target,
                send_settle_mode=SenderSettleMode.Unsettled,
                rcv_settle_mode=ReceiverSettleMode.Second
            ) as link:
                while link.state.value != 3: #'ATTACHED':
                    print(link.state.value)
                    await c.listen()
                for i in range(2):
                    message = Message(data=b'HelloFromPython')
                    await link.send_transfer(message, on_send_complete=message_send_complete, timeout=2)
                await c.listen(wait=2)
                await c.listen(wait=2)
                await c.listen(wait=2)

            await c.listen()

            source = "amqps://{}/{}/ConsumerGroups/$Default/Partitions/0".format(config['hostname'], config['event_hub'])
            print("ATTACHING RECEIVER")
            async with session.create_receiver_link(
                source_address=source,
                send_settle_mode=SenderSettleMode.Unsettled,
                rcv_settle_mode=ReceiverSettleMode.Second,
                max_message_size=1048576,
                on_message_received=message_received,
            ) as link:

                for _ in range(10):
                    print("LISTENING")
                    await c.listen()
                print("DETACHING RECEIVER")
            await c.listen()
            print("ENDING SESSION")
        print("CLOSING")
    print("DONE")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())