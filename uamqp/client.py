#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# pylint: disable=too-many-lines

import logging
import threading
import time
import uuid
import certifi
import queue

from .connection import Connection
from .session import Session
from .sender import SenderLink
from .receiver import ReceiverLink
from .sasl import SASLTransport
from .endpoints import Source, Target

_logger = logging.getLogger(__name__)
_MAX_FRAME_SIZE_BYTES = 64 * 1024


class AMQPClient(object):
    """An AMQP client.

    :param remote_address: The AMQP endpoint to connect to. This could be a send target
     or a receive source.
    :type remote_address: str, bytes or ~uamqp.address.Address
    :param auth: Authentication for the connection. This should be one of the subclasses of
     uamqp.authentication.AMQPAuth. Currently this includes:
        - uamqp.authentication.SASLAnonymous
        - uamqp.authentication.SASLPlain
        - uamqp.authentication.SASTokenAuth
     If no authentication is supplied, SASLAnnoymous will be used by default.
    :type auth: ~uamqp.authentication.common.AMQPAuth
    :param client_name: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type client_name: str or bytes
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param error_policy: A policy for parsing errors on link, connection and message
     disposition to determine whether the error should be retryable.
    :type error_policy: ~uamqp.errors.ErrorPolicy
    :param keep_alive_interval: If set, a thread will be started to keep the connection
     alive during periods of user inactivity. The value will determine how long the
     thread will sleep (in seconds) between pinging the connection. If 0 or None, no
     thread will be started.
    :type keep_alive_interval: int
    :param max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :type max_frame_size: int
    :param channel_max: Maximum number of Session channels in the Connection.
    :type channel_max: int
    :param idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :type idle_timeout: int
    :param properties: Connection properties.
    :type properties: dict
    :param remote_idle_timeout_empty_frame_send_ratio: Ratio of empty frames to
     idle time for Connections with no activity. Value must be between
     0.0 and 1.0 inclusive. Default is 0.5.
    :type remote_idle_timeout_empty_frame_send_ratio: float
    :param incoming_window: The size of the allowed window for incoming messages.
    :type incoming_window: int
    :param outgoing_window: The size of the allowed window for outgoing messages.
    :type outgoing_window: int
    :param handle_max: The maximum number of concurrent link handles.
    :type handle_max: int
    :param on_attach: A callback function to be run on receipt of an ATTACH frame.
     The function must take 4 arguments: source, target, properties and error.
    :type on_attach: func[~uamqp.address.Source, ~uamqp.address.Target, dict, ~uamqp.errors.AMQPConnectionError]
    :param send_settle_mode: The mode by which to settle message send
     operations. If set to `Unsettled`, the client will wait for a confirmation
     from the service that the message was successfully sent. If set to 'Settled',
     the client will not wait for confirmation and assume success.
    :type send_settle_mode: ~uamqp.constants.SenderSettleMode
    :param receive_settle_mode: The mode by which to settle message receive
     operations. If set to `PeekLock`, the receiver will lock a message once received until
     the client accepts or rejects the message. If set to `ReceiveAndDelete`, the service
     will assume successful receipt of the message and clear it from the queue. The
     default is `PeekLock`.
    :type receive_settle_mode: ~uamqp.constants.ReceiverSettleMode
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, hostname, auth=None, **kwargs):
        self._transport = SASLTransport(hostname, auth, ssl={'ca_certs':certifi.where()})
        self._hostname = hostname
        self._auth = auth
        self._name = str(uuid.uuid4())
        self._shutdown = False
        self._connection = None
        self._session = None
        self._link = None
        self._socket_timeout = False

        # Connection settings
        self._max_frame_size = kwargs.pop('max_frame_size', None) or _MAX_FRAME_SIZE_BYTES
        self._channel_max = kwargs.pop('channel_max', None) or 65535
        self._idle_timeout = kwargs.pop('idle_timeout', None)
        self._properties = kwargs.pop('properties', None)

        # Session settings
        self._outgoing_window = kwargs.pop('outgoing_window', None) or _MAX_FRAME_SIZE_BYTES
        self._incoming_window = kwargs.pop('incoming_window', None) or _MAX_FRAME_SIZE_BYTES
        self._handle_max = kwargs.pop('handle_max', None)

        # Link settings
        self._send_settle_mode = kwargs.pop('send_settle_mode', None) or 'UNSETTLED'
        self._receive_settle_mode = kwargs.pop('receive_settle_mode', None) or 'SECOND'
        self._desired_capabilities = kwargs.pop('desired_capabilities', None)

    def __enter__(self):
        """Run Client in a context manager."""
        self.open()
        return self

    def __exit__(self, *args):
        """Close and destroy Client on exiting a context manager."""
        self.close()

    def _client_ready(self):  # pylint: disable=no-self-use
        """Determine whether the client is ready to start sending and/or
        receiving messages. To be ready, the connection must be open and
        authentication complete.

        :rtype: bool
        """
        return True

    def _client_run(self):
        """Perform a single Connection iteration."""
        self._connection.listen(wait=self._socket_timeout)

    def open(self):
        """Open the client. The client can create a new Connection
        or an existing Connection can be passed in. This existing Connection
        may have an existing CBS authentication Session, which will be
        used for this client as well. Otherwise a new Session will be
        created.

        :param connection: An existing Connection that may be shared between
         multiple clients.
        :type connetion: ~uamqp.connection.Connection
        """
        # pylint: disable=protected-access
        if self._session:
            return  # already open.
        _logger.debug("Opening client connection.")
        self._connection = Connection(
            "amqps://" + self._hostname,
            transport=self._transport,
            container_id=self._name,
            max_frame_size=self._max_frame_size,
            channel_max=self._channel_max,
            idle_timeout=self._idle_timeout,
            properties=self._properties)
        self._connection.open()
        self._session = self._connection.begin_session(
            incoming_window=self._incoming_window,
            outgoing_window=self._outgoing_window
        )

    def close(self):
        """Close the client. This includes closing the Session
        and CBS authentication layer as well as the Connection.
        If the client was opened using an external Connection,
        this will be left intact.

        No further messages can be sent or received and the client
        cannot be re-opened.

        All pending, unsent messages will remain uncleared to allow
        them to be inspected and queued to a new client.
        """
        self._shutdown = True
        if not self._session:
            return  # already closed.
        self._connection.end_session(self._session)
        self._session = None
        self._connection.close()

    def auth_complete(self):
        """Whether the authentication handshake is complete during
        connection initialization.

        :rtype: bool
        """
        return True

    def client_ready(self):
        """
        Whether the handler has completed all start up processes such as
        establishing the connection, session, link and authentication, and
        is not ready to process messages.

        :rtype: bool
        """
        if not self.auth_complete():
            return False
        if not self._client_ready():
            try:
                self._connection.listen(wait=self._socket_timeout)
            except ValueError:
                return True
            return False
        return True

    def do_work(self):
        """Run a single connection iteration.
        This will return `True` if the connection is still open
        and ready to be used for further work, or `False` if it needs
        to be shut down.

        :rtype: bool
        :raises: TimeoutError or ~uamqp.errors.ClientTimeout if CBS authentication timeout reached.
        """
        if self._shutdown:
            return False
        if not self.client_ready():
            return True
        return self._client_run()


class SendClient(AMQPClient):
    """An AMQP client for sending messages.

    :param target: The target AMQP service endpoint. This can either be the URI as
     a string or a ~uamqp.address.Target object.
    :type target: str, bytes or ~uamqp.address.Target
    :param auth: Authentication for the connection. This should be one of the subclasses of
     uamqp.authentication.AMQPAuth. Currently this includes:
        - uamqp.authentication.SASLAnonymous
        - uamqp.authentication.SASLPlain
        - uamqp.authentication.SASTokenAuth
     If no authentication is supplied, SASLAnnoymous will be used by default.
    :type auth: ~uamqp.authentication.common.AMQPAuth
    :param client_name: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type client_name: str or bytes
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param msg_timeout: A timeout in milliseconds for messages from when they have been
     added to the send queue to when the message is actually sent. This prevents potentially
     expired data from being sent. If set to 0, messages will not expire. Default is 0.
    :type msg_timeout: int
    :param error_policy: A policy for parsing errors on link, connection and message
     disposition to determine whether the error should be retryable.
    :type error_policy: ~uamqp.errors.ErrorPolicy
    :param keep_alive_interval: If set, a thread will be started to keep the connection
     alive during periods of user inactivity. The value will determine how long the
     thread will sleep (in seconds) between pinging the connection. If 0 or None, no
     thread will be started.
    :type keep_alive_interval: int
    :param send_settle_mode: The mode by which to settle message send
     operations. If set to `Unsettled`, the client will wait for a confirmation
     from the service that the message was successfully sent. If set to 'Settled',
     the client will not wait for confirmation and assume success.
    :type send_settle_mode: ~uamqp.constants.SenderSettleMode
    :param receive_settle_mode: The mode by which to settle message receive
     operations. If set to `PeekLock`, the receiver will lock a message once received until
     the client accepts or rejects the message. If set to `ReceiveAndDelete`, the service
     will assume successful receipt of the message and clear it from the queue. The
     default is `PeekLock`.
    :type receive_settle_mode: ~uamqp.constants.ReceiverSettleMode
    :param max_message_size: The maximum allowed message size negotiated for the Link.
    :type max_message_size: int
    :param link_properties: Metadata to be sent in the Link ATTACH frame.
    :type link_properties: dict
    :param link_credit: The sender Link credit that determines how many
     messages the Link will attempt to handle per connection iteration.
    :type link_credit: int
    :param max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :type max_frame_size: int
    :param channel_max: Maximum number of Session channels in the Connection.
    :type channel_max: int
    :param idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :type idle_timeout: int
    :param properties: Connection properties.
    :type properties: dict
    :param remote_idle_timeout_empty_frame_send_ratio: Ratio of empty frames to
     idle time for Connections with no activity. Value must be between
     0.0 and 1.0 inclusive. Default is 0.5.
    :type remote_idle_timeout_empty_frame_send_ratio: float
    :param incoming_window: The size of the allowed window for incoming messages.
    :type incoming_window: int
    :param outgoing_window: The size of the allowed window for outgoing messages.
    :type outgoing_window: int
    :param handle_max: The maximum number of concurrent link handles.
    :type handle_max: int
    :param on_attach: A callback function to be run on receipt of an ATTACH frame.
     The function must take 4 arguments: source, target, properties and error.
    :type on_attach: func[~uamqp.address.Source, ~uamqp.address.Target, dict, ~uamqp.errors.AMQPConnectionError]
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, hostname, target, auth=None, msg_timeout=0, **kwargs):
        target = Target(target)
        self._msg_timeout = msg_timeout
        self._pending_messages = []
        self._waiting_messages = []
        self._shutdown = None

        # Sender and Link settings
        self._max_message_size = kwargs.pop('max_message_size', None) or constants.MAX_MESSAGE_LENGTH_BYTES
        self._link_properties = kwargs.pop('link_properties', None)
        self._link_credit = kwargs.pop('link_credit', None)
        super(SendClient, self).__init__(hostname, auth=auth, **kwargs)

    def _client_ready(self):
        """Determine whether the client is ready to start sending messages.
        To be ready, the connection must be open and authentication complete,
        The Session, Link and MessageSender must be open and in non-errored
        states.

        :rtype: bool
        :raises: ~uamqp.errors.MessageHandlerError if the MessageSender
         goes into an error state.
        """
        # pylint: disable=protected-access
        if not self._link:
            self._link = self._session.attach_sender_link(
                self._session, 
                target=self.target,
                send_settle_mode=self._send_settle_mode,
                rcv_settle_mode=self._receive_settle_mode,
                max_message_size=self._max_message_size,
                link_credit=self._link_credit,
                properties=self._link_properties)
            self.message_handler.open()
            return False
        if self._link.state.value != 3:  # ATTACHED
            return False
        return True

    def _on_message_sent(self, message, result, delivery_state=None):
        """Callback run on a message send operation. If message
        has a user defined callback, it will be called here. If the result
        of the operation is failure, the message state will be reverted
        to 'pending' up to the maximum retry count.

        :param message: The message that was sent.
        :type message: ~uamqp.message.Message
        :param result: The result of the send operation.
        :type result: int
        :param error: An Exception if an error ocurred during the send operation.
        :type error: ~Exception
        """
        pass
        # try:
        #     exception = delivery_state
        #     result = constants.MessageSendResult(result)
        #     if result == constants.MessageSendResult.Error:
        #         if isinstance(delivery_state, Exception):
        #             exception = errors.ClientMessageError(delivery_state, info=delivery_state)
        #             exception.action = errors.ErrorAction(retry=True)
        #         elif delivery_state:
        #             error = errors.ErrorResponse(delivery_state)
        #             exception = errors._process_send_error(
        #                 self._error_policy,
        #                 error.condition,
        #                 error.description,
        #                 error.info)
        #         else:
        #             exception = errors.MessageSendFailed(constants.ErrorCodes.UnknownError)
        #             exception.action = errors.ErrorAction(retry=True)

        #         if exception.action.retry == errors.ErrorAction.retry \
        #                 and message.retries < self._error_policy.max_retries:
        #             if exception.action.increment_retries:
        #                 message.retries += 1
        #             self._backoff = exception.action.backoff
        #             _logger.debug("Message error, retrying. Attempts: %r, Error: %r", message.retries, exception)
        #             message.state = constants.MessageState.WaitingToBeSent
        #             return
        #         if exception.action.retry == errors.ErrorAction.retry:
        #             _logger.info("Message error, %r retries exhausted. Error: %r", message.retries, exception)
        #         else:
        #             _logger.info("Message error, not retrying. Error: %r", exception)
        #         message.state = constants.MessageState.SendFailed
        #         message._response = exception

        #     else:
        #         _logger.debug("Message sent: %r, %r", result, exception)
        #         message.state = constants.MessageState.SendComplete
        #         message._response = errors.MessageAlreadySettled()
        #     if message.on_send_complete:
        #         message.on_send_complete(result, exception)
        # except KeyboardInterrupt:
        #     _logger.error("Received shutdown signal while processing message send completion.")
        #     self.message_handler._error = errors.AMQPClientShutdown()

    def _get_msg_timeout(self, message):
        current_time = self._counter.get_current_ms()
        elapsed_time = (current_time - message.idle_time)
        if self._msg_timeout > 0 and elapsed_time > self._msg_timeout:
            return None
        return self._msg_timeout - elapsed_time if self._msg_timeout > 0 else 0

    def _transfer_message(self, message, timeout):
        sent = self.message_handler.send(message, self._on_message_sent, timeout=timeout)
        if not sent:
            _logger.info("Message not sent, raising RuntimeError.")
            raise RuntimeError("Message sender failed to add message data to outgoing queue.")

    def _filter_pending(self):
        filtered = []
        for message in self._pending_messages:
            if message.state in constants.DONE_STATES:
                continue
            elif message.state == constants.MessageState.WaitingForSendAck:
                self._waiting_messages += 1
            elif message.state == constants.MessageState.WaitingToBeSent:
                message.state = constants.MessageState.WaitingForSendAck
                try:
                    timeout = self._get_msg_timeout(message)
                    if timeout is None:
                        self._on_message_sent(message, constants.MessageSendResult.Timeout)
                        if message.state != constants.MessageState.WaitingToBeSent:
                            continue
                    else:
                        self._transfer_message(message, timeout)
                except Exception as exp:  # pylint: disable=broad-except
                    self._on_message_sent(message, constants.MessageSendResult.Error, delivery_state=exp)
                    if message.state != constants.MessageState.WaitingToBeSent:
                        continue
            filtered.append(message)
        return filtered

    def _client_run(self):
        """MessageSender Link is now open - perform message send
        on all pending messages.
        Will return True if operation successful and client can remain open for
        further work.

        :rtype: bool
        """
        # pylint: disable=protected-access
        self.message_handler.work()
        self._waiting_messages = 0
        self._pending_messages = self._filter_pending()
        if self._backoff and not self._waiting_messages:
            _logger.info("Client told to backoff - sleeping for %r seconds", self._backoff)
            self._connection.sleep(self._backoff)
            self._backoff = 0
        self._connection.work()
        return True

    @property
    def _message_sender(self):
        """Temporary property to support backwards compatibility
        with EventHubs.
        """
        return self.message_handler

    @property
    def pending_messages(self):
        return [m for m in self._pending_messages if m.state in constants.PENDING_STATES]

    def redirect(self, redirect, auth):
        """Redirect the client endpoint using a Link DETACH redirect
        response.

        :param redirect: The Link DETACH redirect details.
        :type redirect: ~uamqp.errors.LinkRedirect
        :param auth: Authentication credentials to the redirected endpoint.
        :type auth: ~uamqp.authentication.common.AMQPAuth
        """
        if self._ext_connection:
            raise ValueError(
                "Clients with a shared connection cannot be "
                "automatically redirected.")
        if self.message_handler:
            self.message_handler.destroy()
            self.message_handler = None
        self._pending_messages = []
        self._remote_address = address.Target(redirect.address)
        self._redirect(redirect, auth)

    def queue_message(self, *messages):
        """Add one or more messages to the send queue.
        No further action will be taken until either `SendClient.wait()`
        or `SendClient.send_all_messages()` has been called.
        The client does not need to be open yet for messages to be added
        to the queue. Multiple messages can be queued at once:
            - `send_client.queue_message(my_message)`
            - `send_client.queue_message(message_1, message_2, message_3)`
            - `send_client.queue_message(*my_message_list)`

        :param messages: A message to send. This can either be a single instance
         of `Message`, or multiple messages wrapped in an instance of `BatchMessage`.
        :type message: ~uamqp.message.Message
        """
        for message in messages:
            for internal_message in message.gather():
                internal_message.idle_time = self._counter.get_current_ms()
                internal_message.state = constants.MessageState.WaitingToBeSent
                self._pending_messages.append(internal_message)

    def send_message(self, messages, close_on_done=False):
        """Send a single message or batched message.

        :param messages: A message to send. This can either be a single instance
         of `Message`, or multiple messages wrapped in an instance of `BatchMessage`.
        :type message: ~uamqp.message.Message
        :param close_on_done: Close the client once the message is sent. Default is `False`.
        :type close_on_done: bool
        :raises: ~uamqp.errors.MessageException if message fails to send after retry policy
         is exhausted.
        """
        batch = messages.gather()
        pending_batch = []
        for message in batch:
            message.idle_time = self._counter.get_current_ms()
            self._pending_messages.append(message)
            pending_batch.append(message)
        self.open()
        running = True
        try:
            while running and any([m for m in pending_batch if m.state not in constants.DONE_STATES]):
                running = self.do_work()
            failed = [m for m in pending_batch if m.state == constants.MessageState.SendFailed]
            if any(failed):
                details = {"total_messages": len(pending_batch), "number_failed": len(failed)}
                details['failed_messages'] = {}
                exception = None
                for failed_message in failed:
                    exception = failed_message._response  # pylint: disable=protected-access
                    details['failed_messages'][failed_message] = exception
                raise errors.ClientMessageError(exception, info=details)
        finally:
            if close_on_done or not running:
                self.close()

    def messages_pending(self):
        """Check whether the client is holding any unsent
        messages in the queue.

        :rtype: bool
        """
        return bool(self._pending_messages)

    def wait(self):
        """Run the client until all pending message in the queue
        have been processed. Returns whether the client is still running after the
        messages have been processed, or whether a shutdown has been initiated.

        :rtype: bool
        """
        running = True
        while running and self.messages_pending():
            running = self.do_work()
        return running

    def send_all_messages(self, close_on_done=True):
        """Send all pending messages in the queue. This will return a list
        of the send result of all the pending messages so it can be
        determined if any messages failed to send.
        This function will open the client if it is not already open.

        :param close_on_done: Close the client once the messages are sent.
         Default is `True`.
        :type close_on_done: bool
        :rtype: list[~uamqp.constants.MessageState]
        """
        self.open()
        running = True
        try:
            messages = self._pending_messages[:]
            running = self.wait()
            results = [m.state for m in messages]
            return results
        finally:
            if close_on_done or not running:
                self.close()


class ReceiveClient(AMQPClient):
    """An AMQP client for receiving messages.

    :param target: The source AMQP service endpoint. This can either be the URI as
     a string or a ~uamqp.address.Source object.
    :type target: str, bytes or ~uamqp.address.Source
    :param auth: Authentication for the connection. This should be one of the subclasses of
     uamqp.authentication.AMQPAuth. Currently this includes:
        - uamqp.authentication.SASLAnonymous
        - uamqp.authentication.SASLPlain
        - uamqp.authentication.SASTokenAuth
     If no authentication is supplied, SASLAnnoymous will be used by default.
    :type auth: ~uamqp.authentication.common.AMQPAuth
    :param client_name: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type client_name: str or bytes
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param timeout: A timeout in milliseconds. The receiver will shut down if no
     new messages are received after the specified timeout. If set to 0, the receiver
     will never timeout and will continue to listen. The default is 0.
    :type timeout: float
    :param auto_complete: Whether to automatically settle message received via callback
     or via iterator. If the message has not been explicitly settled after processing
     the message will be accepted. Alternatively, when used with batch receive, this setting
     will determine whether the messages are pre-emptively settled during batching, or otherwise
     let to the user to be explicitly settled.
    :type auto_complete: bool
    :param error_policy: A policy for parsing errors on link, connection and message
     disposition to determine whether the error should be retryable.
    :type error_policy: ~uamqp.errors.ErrorPolicy
    :param keep_alive_interval: If set, a thread will be started to keep the connection
     alive during periods of user inactivity. The value will determine how long the
     thread will sleep (in seconds) between pinging the connection. If 0 or None, no
     thread will be started.
    :type keep_alive_interval: int
    :param send_settle_mode: The mode by which to settle message send
     operations. If set to `Unsettled`, the client will wait for a confirmation
     from the service that the message was successfully sent. If set to 'Settled',
     the client will not wait for confirmation and assume success.
    :type send_settle_mode: ~uamqp.constants.SenderSettleMode
    :param receive_settle_mode: The mode by which to settle message receive
     operations. If set to `PeekLock`, the receiver will lock a message once received until
     the client accepts or rejects the message. If set to `ReceiveAndDelete`, the service
     will assume successful receipt of the message and clear it from the queue. The
     default is `PeekLock`.
    :type receive_settle_mode: ~uamqp.constants.ReceiverSettleMode
    :param desired_capabilities: The extension capabilities desired from the peer endpoint.
     To create an desired_capabilities object, please do as follows:
        - 1. Create an array of desired capability symbols: `capabilities_symbol_array = [types.AMQPSymbol(string)]`
        - 2. Transform the array to AMQPValue object: `utils.data_factory(types.AMQPArray(capabilities_symbol_array))`
    :type desired_capabilities: ~uamqp.c_uamqp.AMQPValue
    :param max_message_size: The maximum allowed message size negotiated for the Link.
    :type max_message_size: int
    :param link_properties: Metadata to be sent in the Link ATTACH frame.
    :type link_properties: dict
    :param prefetch: The receiver Link credit that determines how many
     messages the Link will attempt to handle per connection iteration.
     The default is 300.
    :type prefetch: int
    :param max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :type max_frame_size: int
    :param channel_max: Maximum number of Session channels in the Connection.
    :type channel_max: int
    :param idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :type idle_timeout: int
    :param properties: Connection properties.
    :type properties: dict
    :param remote_idle_timeout_empty_frame_send_ratio: Ratio of empty frames to
     idle time for Connections with no activity. Value must be between
     0.0 and 1.0 inclusive. Default is 0.5.
    :type remote_idle_timeout_empty_frame_send_ratio: float
    :param incoming_window: The size of the allowed window for incoming messages.
    :type incoming_window: int
    :param outgoing_window: The size of the allowed window for outgoing messages.
    :type outgoing_window: int
    :param handle_max: The maximum number of concurrent link handles.
    :type handle_max: int
    :param on_attach: A callback function to be run on receipt of an ATTACH frame.
     The function must take 4 arguments: source, target, properties and error.
    :type on_attach: func[~uamqp.address.Source, ~uamqp.address.Target, dict, ~uamqp.errors.AMQPConnectionError]
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, hostname, source, auth=None, **kwargs):
        self.source = Source(address=source)
        self._streaming_receive = False
        self._received_messages = queue.Queue()

        # Sender and Link settings
        self._max_message_size = kwargs.pop('max_message_size', None) or _MAX_FRAME_SIZE_BYTES
        self._link_properties = kwargs.pop('link_properties', None)
        self._link_credit = kwargs.pop('link_credit', None)
        super(ReceiveClient, self).__init__(hostname, auth=auth, **kwargs)

    def _client_ready(self):
        """Determine whether the client is ready to start receiving messages.
        To be ready, the connection must be open and authentication complete,
        The Session, Link and MessageReceiver must be open and in non-errored
        states.

        :rtype: bool
        :raises: ~uamqp.errors.MessageHandlerError if the MessageReceiver
         goes into an error state.
        """
        # pylint: disable=protected-access
        if not self._link:
            self._link = self._session.attach_receiver_link(
                source=self.source,
                link_credit=self._link_credit,
                send_settle_mode=self._send_settle_mode,
                rcv_settle_mode=self._receive_settle_mode,
                max_message_size=self._max_message_size,
                on_message_received=self._message_received,
                properties=self._link_properties)
            return False
        if self._link.state.value != 3:  # ATTACHED
            return False
        return True

    def _client_run(self):
        """MessageReceiver Link is now open - start receiving messages.
        Will return True if operation successful and client can remain open for
        further work.

        :rtype: bool
        """
        try:
            self._connection.listen(wait=self._socket_timeout)
        except ValueError:
            _logger.info("Timeout reached, closing receiver.")
            self._shutdown = True
            return False
        return True

    def _message_received(self, message):
        """Callback run on receipt of every message. If there is
        a user-defined callback, this will be called.
        Additionally if the client is retrieving messages for a batch
        or iterator, the message will be added to an internal queue.

        :param message: Received message.
        :type message: ~uamqp.message.Message
        """
        if self._message_received_callback:
            self._message_received_callback(message)
        if not self._streaming_receive:
            self._received_messages.put(message)
        elif not message.settled:
            # Message was received with callback processing and wasn't settled.
            _logger.info("Message was not settled.")

    def receive_message_batch(self, max_batch_size=None, on_message_received=None, timeout=0):
        """Receive a batch of messages. Messages returned in the batch have already been
        accepted - if you wish to add logic to accept or reject messages based on custom
        criteria, pass in a callback. This method will return as soon as some messages are
        available rather than waiting to achieve a specific batch size, and therefore the
        number of messages returned per call will vary up to the maximum allowed.

        If the receive client is configured with `auto_complete=True` then the messages received
        in the batch returned by this function will already be settled. Alternatively, if
        `auto_complete=False`, then each message will need to be explicitly settled before
        it expires and is released.

        :param max_batch_size: The maximum number of messages that can be returned in
         one call. This value cannot be larger than the prefetch value, and if not specified,
         the prefetch value will be used.
        :type max_batch_size: int
        :param on_message_received: A callback to process messages as they arrive from the
         service. It takes a single argument, a ~uamqp.message.Message object.
        :type on_message_received: callable[~uamqp.message.Message]
        :param timeout: I timeout in milliseconds for which to wait to receive any messages.
         If no messages are received in this time, an empty list will be returned. If set to
         0, the client will continue to wait until at least one message is received. The
         default is 0.
        :type timeout: float
        """
        self._message_received_callback = on_message_received
        max_batch_size = max_batch_size or self._link_credit
        timeout = time.time() + timeout if timeout else 0
        expired = False
        receiving = True
        batch = []
        while not self._received_messages.empty() and len(batch) < max_batch_size:
            batch.append(self._received_messages.get())
            self._received_messages.task_done()
        if len(batch) >= max_batch_size:
            return batch

        while receiving and not expired and len(batch) < max_batch_size:
            while receiving and self._received_messages.qsize() < max_batch_size:
                if timeout and time.time() > timeout:
                    expired = True
                    break
                before = self._received_messages.qsize()
                receiving = self.do_work()
                received = self._received_messages.qsize() - before
                if self._received_messages.qsize() > 0 and received == 0:
                    # No new messages arrived, but we have some - so return what we have.
                    expired = True
                    break
            while not self._received_messages.empty() and len(batch) < max_batch_size:
                batch.append(self._received_messages.get())
                self._received_messages.task_done()
        return batch
