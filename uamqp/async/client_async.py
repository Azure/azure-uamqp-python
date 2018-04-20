#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import collections.abc
import logging
import functools
import uuid
import queue

import uamqp
from uamqp import client
from uamqp import authentication
from uamqp import constants
from uamqp import address
from uamqp import errors

from uamqp.async.connection_async import ConnectionAsync
from uamqp.async.session_async import SessionAsync
from uamqp.async.sender_async import MessageSenderAsync
from uamqp.async.receiver_async import MessageReceiverAsync
from uamqp.authentication import CBSAuthMixin
from uamqp.async.authentication_async import CBSAsyncAuthMixin


_logger = logging.getLogger(__name__)


class AMQPClientAsync(client.AMQPClient):

    def __init__(self, remote_address, auth=None, client_name=None, loop=None, debug=False, **kwargs):
        self.loop = loop or asyncio.get_event_loop()
        super(AMQPClientAsync, self).__init__(
            remote_address, auth=auth, client_name=client_name, debug=debug, **kwargs)

    async def __aenter__(self):
        await self.open_async()
        return self

    async def __aexit__(self, *args):
        await self.close_async()

    async def open_async(self, connection=None):
        if self._session:
            return  # already open
        if connection:
            _logger.debug("Using existing connection.")
            self._auth = connection.auth
            self._ext_connection = True
        self._connection = connection or ConnectionAsync(
            self._hostname,
            self._auth,
            container_id=self._name,
            max_frame_size=self._max_frame_size,
            channel_max=self._channel_max,
            idle_timeout=self._idle_timeout,
            properties=self._properties,
            remote_idle_timeout_empty_frame_send_ratio=self._remote_idle_timeout_empty_frame_send_ratio,
            debug=self._debug_trace,
            loop=self.loop)
        if not self._connection.cbs and isinstance(self._auth, CBSAsyncAuthMixin):
            self._connection.cbs = await self._auth.create_authenticator_async(
                self._connection,
                debug=self._debug_trace,
                loop=self.loop)
            self._session = self._auth._session
        elif self._connection.cbs:
            self._session = self._auth._session
        else:
            self._session = SessionAsync(
                self._connection,
                incoming_window=self._incoming_window,
                outgoing_window=self._outgoing_window,
                handle_max=self._handle_max,
                loop=self.loop)

    async def close_async(self):
        if not self._session:
            return  # already closed.
        else:
            if self._connection.cbs and not self._ext_connection:
                _logger.debug("Closing CBS session.")
                await self._auth.close_authenticator_async()
                self._connection.cbs = None
            elif not self._connection.cbs:
                _logger.debug("Closing non-CBS session.")
                await self._session.destroy_async()
            else:
                _logger.debug("Not closing CBS session.")
            self._session = None
            if not self._ext_connection:
                _logger.debug("Closing unshared connection.")
                await self._connection.destroy_async()
            else:
                _logger.debug("Shared connection remaining open.")
            self._connection = None

    async def mgmt_request_async(self, message, operation, op_type=None, node=None, **kwargs):
        timeout = False
        auth_in_progress = False
        while True:
            if self._connection.cbs:
                timeout, auth_in_progress = await self._auth.handle_token_async()
            if timeout:
                raise TimeoutError("Authorization timeout.")
            elif auth_in_progress:
                await self._connection.work_async()
            else:
                break
        if not self._session:
            raise ValueError("Session not yet open")
        response = await self._session.mgmt_request_async(
            message,
            operation,
            op_type=op_type,
            node=node,
            **kwargs)
        return uamqp.Message(message=response)

    async def do_work_async(self):
        timeout = False
        auth_in_progress = False
        if self._connection.cbs:
            timeout, auth_in_progress = await self._auth.handle_token_async()

        if self._shutdown:
            return False
        if timeout:
            raise TimeoutError("Authorization timeout.")
        elif auth_in_progress:
            await self._connection.work_async()
            return True
        elif not await self._client_ready():
            await self._connection.work_async()
            return True
        else:
            return await self._client_run()


class SendClientAsync(client.SendClient, AMQPClientAsync):

    def __init__(self, target, auth=None, client_name=None, loop=None, debug=False, msg_timeout=0, **kwargs):
        self.loop = loop or asyncio.get_event_loop()
        client.SendClient.__init__(
            self, target, auth=auth, client_name=client_name, debug=debug, msg_timeout=msg_timeout, **kwargs)

    async def _client_ready(self):
        if not self._message_sender:
            self._message_sender = MessageSenderAsync(
                self._session, self._name, self._remote_address,
                name='sender-link-{}'.format(uuid.uuid4()),
                debug=self._debug_trace,
                send_settle_mode=self._send_settle_mode,
                max_message_size=self._max_message_size,
                properties=self._link_properties,
                loop=self.loop)
            await self._message_sender.open_async()
            return False
        elif self._message_sender._state == constants.MessageSenderState.Error:
            raise errors.AMQPConnectionError(
                "Message Sender Client was unable to open. "
                "Please confirm credentials and access permissions."
                "\nSee debug trace for more details.")
        elif self._message_sender._state != constants.MessageSenderState.Open:
            return False
        return True

    async def _client_run(self):
        for message in self._pending_messages[:]:
            if message.state in [constants.MessageState.Complete, constants.MessageState.Failed]:
                try:
                    self._pending_messages.remove(message)
                except ValueError:
                    pass
            elif message.state == constants.MessageState.WaitingToBeSent:
                message.state = constants.MessageState.WaitingForAck
                try:
                    current_time = self._counter.get_current_ms()
                    elapsed_time = (current_time - message.idle_time)/1000
                    if self._msg_timeout > 0 and elapsed_time/1000 > self._msg_timeout:
                        message._on_message_sent(constants.MessageSendResult.Timeout)
                    else:
                        timeout = self._msg_timeout - elapsed_time if self._msg_timeout > 0 else 0
                        self._message_sender.send_async(message, timeout=timeout)

                except Exception as exp:
                    message._on_message_sent(constants.MessageSendResult.Error, error=exp)
        await self._connection.work_async()
        return True

    async def close_async(self):
        if self._message_sender:
            await self._message_sender._destroy_async()
            self._message_sender = None
        await super(SendClientAsync, self).close_async()
        self._pending_messages = []

    async def wait_async(self):
        while self.messages_pending():
            await self.do_work_async()

    async def send_message_async(self, messages, close_on_done=False):
        batch = messages.gather()
        pending_batch = []
        for message in batch:
            message.idle_time = self._counter.get_current_ms()
            self._pending_messages.append(message)
            pending_batch.append(message)
        await self.open_async()
        try:
            while any([m for m in pending_batch if m.state not in constants.DONE_STATES]):
                await self.do_work_async()
        except:
            raise
        else:
            failed = [m for m in pending_batch if m.state == constants.MessageState.Failed]
            if any(failed):
                raise errors.MessageSendFailed("Failed to send message.")
        finally:
            if close_on_done:
                await self.close_async()

    async def send_all_messages_async(self, close_on_done=True):
        await self.open_async()
        try:
            messages = self._pending_messages[:]
            await self.wait_async()
        except:
            raise
        else:
            results = [m.state for m in messages]
            return results
        finally:
            if close_on_done:
                await self.close_async()


class ReceiveClientAsync(client.ReceiveClient, AMQPClientAsync):

    def __init__(self, source, auth=None, client_name=None, loop=None, debug=False, timeout=0, **kwargs):
        self.loop = loop or asyncio.get_event_loop()
        client.ReceiveClient.__init__(
            self, source, auth=auth, client_name=client_name, debug=debug, timeout=timeout, **kwargs)

    async def _client_ready(self):
        if not self._message_receiver:
            self._message_receiver = MessageReceiverAsync(
                self._session, self._remote_address, self._name,
                name='receiver-link-{}'.format(uuid.uuid4()),
                debug=self._debug_trace,
                receive_settle_mode=self._receive_settle_mode,
                prefetch=self._prefetch,
                max_message_size=self._max_message_size,
                properties=self._link_properties,
                loop=self.loop)
            await self._message_receiver.open_async(self)
            return False
        elif self._message_receiver._state == constants.MessageReceiverState.Error:
            raise errors.AMQPConnectionError(
                "Message Receiver Client was unable to open. "
                "Please confirm credentials and access permissions."
                "\nSee debug trace for more details.")
        elif self._message_receiver._state != constants.MessageReceiverState.Open:
            self._last_activity_timestamp = self._counter.get_current_ms()
            return False
        return True

    async def _client_run(self):
        await self._connection.work_async()
        if self._timeout > 0:
            now = self._counter.get_current_ms()
            if self._last_activity_timestamp and not self._was_message_received:
                timespan = now - self._last_activity_timestamp
                if timespan >= self._timeout:
                    _logger.debug("Timeout reached, closing receiver: {}".format(self._remote_address))
                    self._shutdown = True
            else:
                self._last_activity_timestamp = now
        self._was_message_received = False
        return True

    def _message_received(self, message):
        expiry = None
        self._was_message_received = True
        wrapped_message = uamqp.Message(message=message)
        if self._message_received_callback:
            wrapped_message = self._message_received_callback(wrapped_message) or wrapped_message
        if self._received_messages:
            self._received_messages.put(wrapped_message)

    async def receive_messages_async(self, on_message_received):
        await self.open_async()
        self._message_received_callback = on_message_received
        receiving = True
        try:
            while receiving:
                receiving = await self.do_work_async()
        except:
            receiving = False
            raise
        finally:
            if not receiving:
                await self.close_async()

    async def receive_message_batch_async(self, max_batch_size=None, on_message_received=None, timeout=0):
        self._message_received_callback = on_message_received
        max_batch_size = max_batch_size or self._prefetch
        if max_batch_size > self._prefetch:
            raise ValueError(
                'Maximum batch size {} cannot be greater than the '
                'connection prefetch: {}'.format(max_batch_size, self._prefetch))
        timeout = self._counter.get_current_ms() + int(timeout) if timeout else 0
        expired = False
        self._received_messages = self._received_messages or queue.Queue()
        await self.open_async()
        receiving = True
        batch = []
        while not self._received_messages.empty() and len(batch) < max_batch_size:
            batch.append(self._received_messages.get())
            self._received_messages.task_done()
        if len(batch) >= max_batch_size:
            return batch

        while receiving and not expired and len(batch) < max_batch_size:
            while receiving and self._received_messages.qsize() < max_batch_size:
                if timeout > 0 and self._counter.get_current_ms() > timeout:
                    expired = True
                    break
                before = self._received_messages.qsize()
                receiving = await self.do_work_async()
                received = self._received_messages.qsize() - before
                if self._received_messages.qsize() > 0 and received == 0:
                    # No new messages arrived, but we have some - so return what we have.
                    expired = True
                    break

            while not self._received_messages.empty() and len(batch) < max_batch_size:
                batch.append(self._received_messages.get())
                self._received_messages.task_done()
        else:
            return batch

    def receive_messages_iter_async(self, on_message_received=None):
        self._message_received_callback = on_message_received
        self._received_messages = queue.Queue()
        return AsyncMessageIter(self)

    async def close_async(self):
        if self._message_receiver:
            await self._message_receiver._destroy_async()
            self._message_receiver = None
        await super(ReceiveClientAsync, self).close_async()
        self._shutdown = False
        self._last_activity_timestamp = None
        self._was_message_received = False


class AsyncMessageIter(collections.abc.AsyncIterator):

    def __init__(self, client):
        self._client = client
        self.receiving = True

    async def __anext__(self):
        await self._client.open_async()
        try:
            while self.receiving and self._client._received_messages.empty():
                self.receiving = await self._client.do_work_async()
            if not self._client._received_messages.empty():
                message = self._client._received_messages.get()
                self._client._received_messages.task_done()
                return message
            else:
                raise StopAsyncIteration("Message receive closing.")
        except:
            self.receiving = False
            raise
        finally:
            if not self.receiving:
                await self._client.close_async()
