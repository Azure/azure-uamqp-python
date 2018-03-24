#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid
import queue
import functools
import time
try:
    from urllib import unquote_plus
except Exception:
    from urllib.parse import unquote_plus

import uamqp
from uamqp import authentication
from uamqp import constants
from uamqp import sender
from uamqp import receiver
from uamqp import address
from uamqp import errors
from uamqp import c_uamqp
from uamqp import Connection
from uamqp import Session


_logger = logging.getLogger(__name__)


class AMQPClient:

    def __init__(self, remote_address, auth=None, client_name=None, debug=False, **kwargs):
        self._remote_address = remote_address if isinstance(remote_address, address.Address) \
            else address.Address(remote_address)
        self._hostname = self._remote_address.parsed_address.hostname
        if not auth:
            username = self._remote_address.parsed_address.username
            password = self._remote_address.parsed_address.password
            if username and password:
                username = unquote_plus(username)
                password = unquote_plus(password)
                auth = authentication.SASLPlain(self._hostname, username, password)

        self._auth = auth if auth else authentication.SASLAnonymous(self._hostname)
        self._name = client_name if client_name else str(uuid.uuid4())
        self._debug_trace = debug
        self._counter = c_uamqp.TickCounter()
        self._shutdown = False
        self._connection = None
        self._ext_connection = False
        self._session = None

        # Connection settings
        self._max_frame_size = kwargs.pop('max_frame_size', None) or constants.MAX_FRAME_SIZE_BYTES
        self._channel_max = kwargs.pop('channel_max', None)
        self._idle_timeout = kwargs.pop('idle_timeout', None)
        self._properties = kwargs.pop('properties', None)
        self._remote_idle_timeout_empty_frame_send_ratio = kwargs.pop('remote_idle_timeout_empty_frame_send_ratio', None)

        # Session settings
        self._outgoing_window = kwargs.pop('outgoing_window', None) or constants.MAX_FRAME_SIZE_BYTES
        self._incoming_window = kwargs.pop('incoming_window', None) or constants.MAX_FRAME_SIZE_BYTES
        self._handle_max = kwargs.pop('handle_max', None)

        if kwargs:
            raise ValueError("Received unrecognized kwargs: {}".format(", ".join(kwargs.keys())))

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def _client_ready(self):
        return True

    def _client_run(self):
        self._connection.work()

    def open(self, connection=None):
        if self._session:
            return  # already open.
        _logger.debug("Opening client connection.")
        if connection:
            _logger.debug("Using existing connection.")
            self._auth = connection.auth
            self._ext_connection = True
        self._connection = connection or Connection(
            self._hostname,
            self._auth,
            container_id=self._name,
            max_frame_size=self._max_frame_size,
            channel_max=self._channel_max,
            idle_timeout=self._idle_timeout,
            properties=self._properties,
            remote_idle_timeout_empty_frame_send_ratio=self._remote_idle_timeout_empty_frame_send_ratio,
            debug=self._debug_trace)
        if not self._connection.cbs and isinstance(self._auth, authentication.CBSAuthMixin):
            self._connection.cbs = self._auth.create_authenticator(
                self._connection,
                debug=self._debug_trace)
            self._session = self._auth._session
        elif self._connection.cbs:
            self._session = self._auth._session
        else:
            self._session = Session(
                self._connection,
                incoming_window=self._incoming_window,
                outgoing_window=self._outgoing_window,
                handle_max=self._handle_max)

    def close(self):
        if not self._session:
            return  # already closed.
        else:
            if self._connection.cbs and not self._ext_connection:
                self._auth.close_authenticator()
                self._connection.cbs = None
            elif not self._connection.cbs:
                self._session.destroy()
            self._session = None
            if not self._ext_connection:
                self._connection.destroy()
            self._connection = None

    def mgmt_request(self, message, operation, op_type=None, node=None, **kwargs):
        timeout = False
        auth_in_progress = False
        while True:
            if self._connection.cbs:
                timeout, auth_in_progress = self._auth.handle_token()
            if timeout:
                raise TimeoutError("Authorization timeout.")
            elif auth_in_progress:
                self._connection.work()
            else:
                break
        if not self._session:
            raise ValueError("Session not yet open")
        response = self._session.mgmt_request(
            message,
            operation,
            op_type=op_type,
            node=node,
            **kwargs)
        return uamqp.Message(message=response)

    def do_work(self):
        timeout = False
        auth_in_progress = False
        if self._connection.cbs:
            timeout, auth_in_progress = self._auth.handle_token()
        if self._shutdown:
            return False
        if timeout:
            raise TimeoutError("Authorization timeout.")
        elif auth_in_progress:
            self._connection.work()
            return True
        elif not self._client_ready():
            self._connection.work()
            return True
        else:
            return self._client_run()


class SendClient(AMQPClient):

    def __init__(self, target, auth=None, client_name=None, debug=False, msg_timeout=0, **kwargs):
        target = target if isinstance(target, address.Address) else address.Target(target)
        self._msg_timeout = msg_timeout
        self._pending_messages = []
        self._message_sender = None
        self._shutdown = None

        # Sender and Link settings
        self._send_settle_mode = kwargs.pop('send_settle_mode', None) or constants.SenderSettleMode.Unsettled
        self._max_message_size = kwargs.pop('max_message_size', None) or constants.MAX_MESSAGE_LENGTH_BYTES
        self._link_properties = kwargs.pop('link_properties', None)
        super(SendClient, self).__init__(target, auth=auth, client_name=client_name, debug=debug, **kwargs)

    def _client_ready(self):
        if not self._message_sender:
            self._message_sender = sender.MessageSender(
                self._session, self._name, self._remote_address,
                name='sender-link-{}'.format(uuid.uuid4()),
                debug=self._debug_trace,
                send_settle_mode=self._send_settle_mode,
                max_message_size=self._max_message_size,
                properties=self._link_properties)
            self._message_sender.open()
            return False
        elif self._message_sender._state == constants.MessageSenderState.Error:
            raise ValueError("Message sender in error state.")
        elif self._message_sender._state != constants.MessageSenderState.Open:
            return False
        return True

    def _client_run(self):
        for message in self._pending_messages[:]:
            if message.state == constants.MessageState.Complete:
                try:
                    self._pending_messages.remove(message)
                except ValueError:
                    pass
            elif message.state == constants.MessageState.WaitingToBeSent:
                message.state = constants.MessageState.WaitingForAck
                try:
                    current_time = self._counter.get_current_ms()
                    elapsed_time = (current_time - message.idle_time)/1000
                    if self._msg_timeout > 0 and elapsed_time > self._msg_timeout:
                        message._on_message_sent(constants.MessageSendResult.Timeout)
                    else:
                        timeout = self._msg_timeout - elapsed_time if self._msg_timeout > 0 else 0
                        self._message_sender.send_async(message, timeout=timeout)
                except Exception as exp:
                    message._on_message_sent(constants.MessageSendResult.Error, error=exp)
        self._connection.work()
        return True

    def close(self):
        if self._message_sender:
            self._message_sender._destroy()
            self._message_sender = None
        super(SendClient, self).close()
        self._pending_messages = []

    def queue_message(self, message):
        message.idle_time = self._counter.get_current_ms()
        self._pending_messages.append(message)

    def send_message(self, message, close_on_done=False):
        message.idle_time = self._counter.get_current_ms()
        self._pending_messages.append(message)
        self.open()
        try:
            while message.state != constants.MessageState.Complete:
                self.do_work()
        except:
            raise
        finally:
            if close_on_done:
                self.close()

    def messages_pending(self):
        return bool(self._pending_messages)

    def wait(self):
        while self.messages_pending():
            self.do_work()

    def send_all_messages(self, close_on_done=True):
        self.open()
        try:
            self.wait()
        except:
            raise
        finally:
            if close_on_done:
                self.close()


class ReceiveClient(AMQPClient):

    def __init__(self, source, auth=None, client_name=None, debug=False, timeout=0, **kwargs):
        source = source if isinstance(source, address.Address) else address.Source(source)
        self._timeout = timeout
        self._message_receiver = None
        self._last_activity_timestamp = None
        self._was_message_received = False
        self._message_received_callback = None
        self._received_messages = None

        # Receiver and Link settings
        self._receive_settle_mode = kwargs.pop('receive_settle_mode', None) or constants.ReceiverSettleMode.PeekLock
        self._max_message_size = kwargs.pop('max_message_size', None) or constants.MAX_MESSAGE_LENGTH_BYTES
        self._prefetch = kwargs.pop('prefetch', None) or 300
        self._link_properties = kwargs.pop('link_properties', None)
        super(ReceiveClient, self).__init__(source, auth=auth, client_name=client_name, debug=debug, **kwargs)

    def _client_ready(self):
        if not self._message_receiver:
            self._message_receiver = receiver.MessageReceiver(
                self._session, self._remote_address, self._name,
                name='receiver-link',
                debug=self._debug_trace,
                receive_settle_mode=self._receive_settle_mode,
                prefetch=self._prefetch,
                max_message_size=self._max_message_size,
                properties=self._link_properties)
            self._message_receiver.open(self)
            return False
        elif self._message_receiver._state == constants.MessageReceiverState.Error:
            raise ValueError("Message receiver in error state.")
        elif self._message_receiver._state != constants.MessageReceiverState.Open:
            self._last_activity_timestamp = self._counter.get_current_ms()
            return False
        return True

    def _client_run(self):
        self._connection.work()
        if self._timeout > 0:
            now = self._counter.get_current_ms()
            if self._last_activity_timestamp and not self._was_message_received:
                timespan = now - self._last_activity_timestamp
                if timespan >= self._timeout:
                    _logger.debug("Timeout reached, closing receiver.")
                    self._shutdown = True
            else:
                self._last_activity_timestamp = now
        self._was_message_received = False
        return True

    def _message_received(self, message):
        self._was_message_received = True
        wrapped_message = uamqp.Message(message=message)
        if self._message_received_callback:
            wrapped_message = self._message_received_callback(wrapped_message) or wrapped_message
        if self._received_messages:
             self._received_messages.put(wrapped_message)

    def receive_message_batch(self, batch_size=None, on_message_received=None, timeout=0):
        self._message_received_callback = on_message_received
        batch_size = batch_size or self._prefetch
        timeout = self._counter.get_current_ms() + timeout if timeout else 0
        expired = False
        self._received_messages = self._received_messages or queue.Queue(self._prefetch)
        self.open()
        receiving = True
        batch = []
        while not self._received_messages.empty() and len(batch) < batch_size:
            batch.append(self._received_messages.get())
            self._received_messages.task_done()
        if len(batch) >= batch_size:
            return batch
        while receiving and not expired and len(batch) < batch_size:
            while receiving and self._received_messages.qsize() < min(batch_size, self._prefetch):
                if timeout > 0 and self._counter.get_current_ms() > timeout:
                    expired = True
                    break
                receiving = self.do_work()
            while not self._received_messages.empty() and len(batch) < batch_size:
                batch.append(self._received_messages.get())
                self._received_messages.task_done()
        else:
            return batch

    def receive_messages(self, on_message_received, close_on_done=True):
        self.open()
        self._message_received_callback = on_message_received
        receiving = True
        try:
            while receiving:
                receiving = self.do_work()
        except:
            raise
        finally:
            if close_on_done:
                self.close()

    def close(self):
        if self._message_receiver:
            self._message_receiver._destroy()
            self._message_receiver = None
        super(ReceiveClient, self).close()
        self._shutdown = False
        self._last_activity_timestamp = None
        self._was_message_received = False
