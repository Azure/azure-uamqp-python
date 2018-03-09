#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid
import queue
import threading
import functools

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


class SendClient:

    def __init__(self, target, auth=None, client_name=None, debug=False, msg_timeout=0, **kwargs):
        self._target = target if isinstance(target, address.AddressMixin) else address.Target(target)
        self._hostname = self._target.parsed_address.hostname
        if not auth:
            username = self._target.parsed_address.username
            password = self._target.parsed_address.password
            if username and password:
                auth = authentication.SASLPlain(self._hostname, username, password)

        self._auth = auth if auth else authentication.SASLAnonymous(self._hostname)
        self._name = client_name if client_name else str(uuid.uuid4())
        self._debug_trace = debug
        self._msg_timeout = msg_timeout
        self._counter = c_uamqp.TickCounter()
        self._cbs_handle = None
        self._pending_messages = []
        self._message_sent_callback = None
        self._daemon = None

        self._connection = None
        self._ext_connection = False
        self._session = None
        self._message_sender = None
        self._shutdown = None

        # Connection settings
        self._max_frame_size = kwargs.pop('max_frame_size', constants.MAX_FRAME_SIZE_BYTES)
        self._channel_max = kwargs.pop('channel_max', None)
        self._idle_timeout = kwargs.pop('idle_timeout', None)
        self._properties = kwargs.pop('properties', None)
        self._remote_idle_timeout_empty_frame_send_ratio = kwargs.pop('remote_idle_timeout_empty_frame_send_ratio', None)

        # Session settings
        self._outgoing_window = kwargs.pop('outgoing_window', constants.MAX_FRAME_SIZE_BYTES)
        self._handle_max = kwargs.pop('handle_max', None)

        # Sender and Link settings
        self._send_settle_mode = kwargs.pop('send_settle_mode', constants.SenderSettleMode.Unsettled)
        self._max_message_size = kwargs.pop('max_message_size', constants.MAX_MESSAGE_LENGTH_BYTES)

        if kwargs:
            raise ValueError("Received unrecognized kwargs: {}".format(", ".join(kwargs.keys())))

    def _run_background(self, connection=None):
        self.open(connection=connection)
        try:
            while not self._shutdown.is_set():
                self.wait()
            self.close(is_daemon=True)
        except Exception as e:
            _logger.debug("Error: {}".format(e))
            raise e
        finally:
            self.close(is_daemon=True)

    def open(self, connection=None):
        if self._session:
            return  # already open.
        _logger.debug("Opening client conneciton.")
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
        self._session = Session(
            self._connection,
            outgoing_window=self._outgoing_window,
            handle_max=self._handle_max)
        if isinstance(self._auth, authentication.CBSAuthMixin):
            self._cbs_handle = self._auth.create_authenticator(self._session)

    def close(self, is_daemon=False):
        if not self._session:
            return  # already closed.
        if self._daemon and not is_daemon:
            self.stop_daemon()
        else:
            _logger.debug("Closing client.")
            if self._message_sender:
                self._message_sender._destroy()
                self._message_sender = None
            if self._cbs_handle:
                self._auth.close_authenticator()
                self._cbs_handle = None
            self._session.destroy()
            self._session = None
            if not self._ext_connection:
                _logger.debug("Closing connection.")
                self._connection.destroy()
                self._connection = None
            self._pending_messages = []

    def queue_message(self, message):
        message.idle_time = self._counter.get_current_ms()
        self._pending_messages.append(message)

    def run_daemon(self, connection=None):
        if self._session:
            raise ValueError("SendClient is already open.")
        _logger.info("Starting SendClient daemon")
        self._shutdown = threading.Event()
        self._daemon = threading.Thread(target=functools.partial(self._run_background, connection=connection))
        self._daemon.daemon = True
        self._daemon.start()

    def stop_daemon(self):  #TODO: Implement force close
        if not self._daemon or not self._shutdown:
            raise ValueError("No daemon running.")
        if self._shutdown.is_set():
            raise ValueError("Daemon has already stopped.")
        self._shutdown.set()
        self._daemon.join()
        self._daemon = None
        self._shutdown = None

    def wait(self):
        while self._pending_messages:
            self.do_work()

    def send_all_messages(self):
        self.open()
        try:
            self.wait()
        except:
            raise
        finally:
            self.close()

    def do_work(self):
        timeout = False
        auth_in_progress = False
        if self._cbs_handle:
            timeout, auth_in_progress = self._auth.handle_token()

        if timeout:
            raise TimeoutError("Authorization timeout.")
        elif auth_in_progress:
            self._connection.work()

        elif not self._message_sender:
            self._message_sender = sender.MessageSender(
                self._session, self._name, self._target,
                name='sender-link',
                debug=self._debug_trace,
                send_settle_mode=self._send_settle_mode,
                max_message_size=self._max_message_size)
            self._message_sender.open()
            self._connection.work()

        elif self._message_sender._state == constants.MessageSenderState.Error:
            raise ValueError("Message sender in error state.")

        elif self._message_sender._state != constants.MessageSenderState.Open:
            self._connection.work()

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
                        if self._msg_timeout > 0 and elapsed_time > self._msg_timeout:
                            message._on_message_sent(constants.MessageSendResult.Timeout)
                        else:
                            timeout = self._msg_timeout - elapsed_time if self._msg_timeout > 0 else 0
                            self._message_sender.send_async(message, timeout=timeout)

                    except Exception as exp:
                        message._on_message_sent(constants.MessageSendResult.Error, error=exp)
            self._connection.work()


class ReceiveClient:

    def __init__(self, source, auth=None, client_name=None, debug=False, timeout=0, **kwargs):
        self._source = source if isinstance(source, address.AddressMixin) else address.Source(source)
        self._hostname = self._source.parsed_address.hostname
        if not auth:
            username = self._target.parsed_address.username
            password = self._target.parsed_address.password
            if username and password:
                auth = authentication.SASLPlain(self._hostname, username, password)

        self._auth = auth or authentication.SASLAnonymous(self._hostname)
        self._name = client_name if client_name else str(uuid.uuid4())
        self._debug_trace = debug
        self._timeout = timeout
        self._counter = c_uamqp.TickCounter()
        self._cbs_handle = None
        self._count = 0
        self._daemon = None
        self._close_daemon = None

        self._connection = None
        self._ext_connection = False
        self._session = None
        self._message_receiver = None
        self._shutdown = False
        self._last_activity_timestamp = None
        self._was_message_received = False
        self._message_received_callback = None
        self._received_messages = None

        # Connection settings
        self._max_frame_size = kwargs.pop('max_frame_size', constants.MAX_FRAME_SIZE_BYTES)
        self._channel_max = kwargs.pop('channel_max', None)
        self._idle_timeout = kwargs.pop('idle_timeout', None)
        self._properties = kwargs.pop('properties', None)
        self._remote_idle_timeout_empty_frame_send_ratio = kwargs.pop('remote_idle_timeout_empty_frame_send_ratio', None)

        # Session settings
        self._incoming_window = kwargs.pop('incoming_window', constants.MAX_FRAME_SIZE_BYTES)
        self._handle_max = kwargs.pop('handle_max', None)

        # Receiver and Link settings
        self._receive_settle_mode = kwargs.pop('receive_settle_mode', constants.ReceiverSettleMode.PeekLock)
        self._max_message_size = kwargs.pop('max_message_size', constants.MAX_MESSAGE_LENGTH_BYTES)
        self._prefetch = kwargs.pop('prefetch', 0)
        self._max_count = kwargs.pop('max_count', None)

        if kwargs:
            raise ValueError("Received unrecognized kwargs: {}".format(", ".join(kwargs.keys())))

    def _message_received(self, message):
        self._was_message_received = True
        if self._max_count is not None:
            self._count += 1
        wrapped_message = uamqp.Message(message=message)
        if self._message_received_callback:
            self._message_received_callback(wrapped_message)
        if self._received_messages:
             self._received_messages.put(wrapped_message)

    def _message_generator(self):
        receiving = True
        while receiving:
            while receiving and self._received_messages.empty():
                receiving = self.do_work()
            try:
                for message in iter(self._received_messages.get_nowait, None):
                    yield message
            except queue.Empty:
                continue

    def _run_background(self, on_message_received, connection=None):
        self.open(connection=connection)
        self._message_received_callback = on_message_received
        try:
            receiving = True
            while not self._close_daemon.is_set() and receiving:
                receiving = self.do_work()
        except Exception as e:
            return e
        finally:
            self.close()

    def receive_messages_iter(self, on_message_received=None):
        if self._daemon:
            raise ValueError("This function is not supported while daemon is running.")
        self._message_received_callback = on_message_received
        self._received_messages = queue.Queue(self._prefetch)
        if not self._session:
            self.open()
        return self._message_generator()

    def receive_messages(self, on_message_received, close_on_done=True):
        if not self._session:
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

    def open(self, connection=None):
        if self._session:
            raise ValueError("ReceiveClient is already open.")
        if connection:
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
        self._session = Session(
            self._connection,
            incoming_window=self._incoming_window,
            handle_max=self._handle_max)
        if isinstance(self._auth, authentication.CBSAuthMixin):
            self._cbs_handle = self._auth.create_authenticator(self._session)

    def close(self):
        if not self._session:
            raise ValueError("ReceiveClient is already closed.")
        if self._daemon and not self._close_daemon.is_set():
            self.stop_daemon()
        else:
            if self._message_receiver:
                self._message_receiver._destroy()
                self._message_receiver = None
            if self._cbs_handle:
                self._auth.close_authenticator()
                self._cbs_handle = None
            self._session.destroy()
            self._session = None
            if self._ext_connection:
                self._connection.destroy()
                self._connection = None
            self._shutdown = False
            self._last_activity_timestamp = None
            self._was_message_received = False

    def run_daemon(self, on_message_received, connection=None):
        if self._session:
            raise ValueError("ReceiveClient is already open.")
        _logger.info("Starting ReceiveClient daemon")
        self._close_daemon = threading.Event()
        self._daemon = threading.Thread(target=functools.partial(self._run_background, on_message_received, connection=connection))
        self._daemon.daemon = True
        self._daemon.start()

    def stop_daemon(self):  #TODO: Implement force close
        if not self._daemon or not self._close_daemon:
            raise ValueError("No daemon running.")
        self._close_daemon.set()
        self._daemon.join()
        self._daemon = None
        self._shutdown = None

    def do_work(self):
        timeout = False
        auth_in_progress = False
        if self._cbs_handle:
            timeout, auth_in_progress = self._auth.handle_token()

        if self._shutdown:
            return False

        if timeout:
            raise TimeoutError("Authorization timeout.")

        elif auth_in_progress:
            self._connection.work()

        elif not self._message_receiver:
            self._message_receiver = receiver.MessageReceiver(
                self._session, self._source, self._name,
                name='receiver-link',
                debug=self._debug_trace,
                receive_settle_mode=self._receive_settle_mode,
                prefetch=self._prefetch,
                max_message_size=self._max_message_size)
            self._message_receiver.open(self)
            self._connection.work()

        elif self._message_receiver._state == constants.MessageReceiverState.Error:
            raise ValueError("Message receiver in error state.")

        elif self._message_receiver._state != constants.MessageReceiverState.Open:
            self._connection.work()
            self._last_activity_timestamp = self._counter.get_current_ms()

        else:
            self._connection.work()
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
