#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
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


class SendClientAsync(client.SendClient):

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
            debug=self._debug_trace)
        self._session = SessionAsync(
            self._connection,
            outgoing_window=self._outgoing_window,
            handle_max=self._handle_max)
        if isinstance(self._auth, CBSAsyncAuthMixin):
            self._cbs_handle = await self._auth.create_authenticator_async(self._session)
        elif isinstance(self._auth, authentication.CBSAuthMixin):
            raise ValueError("Token authentication must use asynchrnous base with an asynchronous client.")

    async def close_async(self):
        if not self._session:
            return  # already closed.
        else:
            if self._message_sender:
                await self._message_sender._destroy_async()
                self._message_sender = None
            if self._cbs_handle:
                await self._auth.close_authenticator_async()
                self._cbs_handle = None
            await self._session.destroy_async()
            self._session = None
            if not self._ext_connection:
                await self._connection.destroy_async()
                self._connection = None
            self._pending_messages = []

    async def wait_async(self):
        while self.messages_pending():
            await self.do_work_async()

    async def send_message_async(self, message, close_on_done=False):
        message.idle_time = self._counter.get_current_ms()
        self._pending_messages.append(message)
        await self.open_async()
        try:
            while message.state != constants.MessageState.Complete:
                await self.do_work_async()
        except:
            raise
        else:
            if close_on_done:
                await self.close_async()

    async def send_all_messages_async(self, close_on_done=True):
        await self.open_async()
        try:
            await self.wait_async()
        except:
            raise
        finally:
            if close_on_done:
                await self.close_async()

    async def do_work_async(self):
        timeout = False
        auth_in_progress = False
        if self._cbs_handle:
            timeout, auth_in_progress = await self._auth.handle_token_async()

        if timeout:
            raise TimeoutError("Authorization timeout.")

        elif auth_in_progress:
            await self._connection.work_async()

        elif not self._message_sender:
            self._message_sender = MessageSenderAsync(
                self._session, self._name, self._target,
                name='sender-link',
                debug=self._debug_trace,
                send_settle_mode=self._send_settle_mode,
                max_message_size=self._max_message_size)
            await self._message_sender.open_async()
            await self._connection.work_async()

        elif self._message_sender._state == constants.MessageSenderState.Error:
            raise ValueError("Message sender in error state.")

        elif self._message_sender._state != constants.MessageSenderState.Open:
            await self._connection.work_async()

        else:
            for message in self._pending_messages[:]:
                if message.state == constants.MessageState.Complete:
                    try:
                        self._pending_messages.remove(message)
                    except ValueError:
                        pass
                elif message.state == constants.MessageState.WaitingToBeSent:
                    message.state = constants.MessageState.WaitingForAck
                    if not message.on_send_complete:
                        message.on_send_complete = self._message_sent_callback
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


class ReceiveClientAsync(client.ReceiveClient):

    async def receive_messages_async(self, on_message_received, close_on_done=True):
        await self.open_async()
        self._message_received_callback = on_message_received
        receiving = True
        try:
            while receiving:
                receiving = await self.do_work_async()
        except:
            raise
        finally:
            if close_on_done:
                await self.close_async()

    async def open_async(self, connection=None):
        if self._session:
            return  # Already open
        if connection:
            self._auth = connection.auth
            self._ext_connection = True
        self._connection = connection or ConnectionAsync(
            self._hostname,
            self._auth,
            container_id=self._name,
            max_frame_size=self._max_frame_size,
            channel_max=self._channel_max,
            idle_timeout=self._idle_timeout,
            remote_idle_timeout_empty_frame_send_ratio=self._remote_idle_timeout_empty_frame_send_ratio,
            debug=self._debug_trace)
        self._session = SessionAsync(
            self._connection,
            incoming_window=self._incoming_window,
            handle_max=self._handle_max)
        if isinstance(self._auth, authentication.CBSAuthMixin):
            self._cbs_handle = await self._auth.create_authenticator_async(self._session)
        elif isinstance(self._auth, authentication.CBSAuthMixin):
            raise ValueError("Token authentication must use asynchrnous base with an asynchronous client.")

    async def close_async(self):
        if not self._session:
            return  # Already closed
        else:
            if self._message_receiver:
                await self._message_receiver._destroy_async()
                self._message_receiver = None
            if self._cbs_handle:
                await self._auth.close_authenticator_async()
                self._cbs_handle = None
            await self._session.destroy_async()
            self._session = None
            if not self._ext_connection:
                await self._connection.destroy_async()
                self._connection = None
            self._shutdown = False
            self._last_activity_timestamp = None
            self._was_message_received = False

    async def do_work_async(self):
        timeout = False
        auth_in_progress = False
        if self._cbs_handle:
            timeout, auth_in_progress = await self._auth.handle_token_async()

        if self._shutdown:
            await self.close_async()
            return False

        if timeout:
            raise TimeoutError("Authorization timeout.")

        elif auth_in_progress:
            await self._connection.work_async()

        elif not self._message_receiver:
            self._message_receiver = MessageReceiverAsync(
                self._session, self._source, self._name,name='receiver-link',
                debug=self._debug_trace,
                receive_settle_mode=self._receive_settle_mode,
                prefetch=self._prefetch,
                max_message_size=self._max_message_size)
            await self._message_receiver.open_async(self)
            await self._connection.work_async()

        elif self._message_receiver._state == constants.MessageReceiverState.Error:
            raise ValueError("Message receiver in error state.")

        elif self._message_receiver._state != constants.MessageReceiverState.Open:
            await self._connection.work_async()
            self._last_activity_timestamp = self._counter.get_current_ms()

        else:
            await self._connection.work_async()
            if self._max_count is not None and self._count >= self._max_count:
                self._shutdown = True
            if self._timeout > 0:
                now = self._counter.get_current_ms()
                if not self._was_message_received:
                    timespan = now - self._last_activity_timestamp
                    if timespan >= self._timeout:
                        _logger.debug("Timeout reached, closing receiver.")
                        self._shutdown = True
                else:
                    self._last_activity_timestamp = now
            self._was_message_received = False

        return True