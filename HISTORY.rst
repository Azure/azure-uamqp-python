.. :changelog:

Release History
===============

0.2.0 (2018-07-25)
++++++++++++++++++

- **Breaking change** `MessageSender.send_async` has been renamed to `MessageSender.send`, and
  `MessageSenderAsync.send_async` is now a coroutine.
- **Breaking change** Removed `detach_received` callback argument from MessageSender, MessageReceiver,
  MessageSenderAsync, and MessageReceiverAsync in favour of new `error_policy` argument.
- Added ErrorPolicy class to determine how the client should respond to both generic AMQP errors
  and custom or vendor-specific errors. A default policy will be used, but a custom policy can
  be added to any client by using a new `error_policy` argument. Value must be either an instance
  or subclass of ErrorPolicy.

    - The `error_policy` argument has also been added to MessageSender, MessageReceiver, Connection, and their
      async counterparts to allow for handling of link DETACH and connection CLOSE events.
    - The error policy passed to a SendClient determines the number of message send retry
      attempts. This replaces the previous `constants.MESSAGE_SEND_RETRIES` value which is now
      deprecated.
    - Added new ErrorAction object to determine how a client should respond to an error. It has
      three properties: `retry` (a boolean to determine whether the error is retryable), `backoff`
      (an integer to determine how long the client should wait before retrying, default is 0) and
      `increment_retries` (a boolean to determine whether the error should count against the maximum
      retry attempts, default is `True`). Currently `backoff` and `increment_retries` are only
      considered for message send failures.
    - Added `VendorConnectionClose` and `VendorLinkDetach` exceptions for non-standard (unrecognized)
      connection/link errors.

- Added support for HTTP proxy configuration.
- Added support for running async clients synchronously.
- Added keep-alive support for connection - this is a background thread for a synchronous
  client, and a background async function for an async client. The keep-alive feature is
  disabled by default, to enable, set the `keep_alive_interval` argument on the client to
  an integer representing the number of seconds between connection pings.
- Added support for catching a Connection CLOSE event.
- Added support for `Connection.sleep` and `ConnectionAsync.sleep_async` to pause the connection.
- Added support for surfacing message disposition delivery-state (with error information).
- Added `constants.ErrorCodes` enum to map standard AMQP error conditions. This replaces the previous
  `constants.ERROR_CONNECTION_REDIRECT` and `constants.ERROR_LINK_REDIRECT` which are now both
  deprecated.
- Added new super error `AMQPError` from which all exceptions inherit.
- Added new `MessageHandlerError` exception, a subclass of `AMQPConnectionError`, for
  Senders/Receivers that enter an indeterminate error state.
- `MessageException` is now a subclass of `MessageResponse`.
- Added `ClientMessageError` exception, a subclass of `MessageException` for send errors raised client-side.
- Catching Link DETACH event will now work regardless of whether service returns delivery-state.
- Fixed bug where received messages attempting to settle on a detached link crashed the client.
- Fixed bug in amqp C DescribedValue.
- Fixed bug where client crashed on deallocating failed management operation.


0.1.1 (2018-07-14)
++++++++++++++++++

- Removed circular dependency in Python 3.4 with types.py/utils.py
- When a header properties is not set, returns `None` rather than raising ValueError.
- Fixed bug in receiving messages with application properties.


0.1.0 (2018-07-05)
++++++++++++++++++

- Fixed bug in error handling for CBS auth to invalid hostname.
- Changed C error logging to debug level.
- Bumped uAMQP C version to 1.2.7
- Fixed memory leaks and deallocation bugs with Properties and Annotations.


0.1.0rc2 (2018-07-02)
+++++++++++++++++++++

- **Breaking change** Submodule `async` has been renamed to the internal `_async`.
  All asynchronous classes in the submodule can now be accessed from uamqp or uamqp.authentication directly.
- **Breaking change** Anything returned by a callback supplied to receive messages will now be ignored.
- **Breaking change** Changed message state enum values:

    - `Complete -> SendComplete`
    - `Failed -> SendFailed`
    - `WaitingForAck -> WaitingForSendAck`

- Added new message state enum values:

    - `ReceivedUnsettled`
    - `ReceivedSettled`

- **Breaking change** Changes to message settlement exceptions:

    - Combined the `AbandonMessage` and `DeferMessage` exceptions as `MessageModified` to be in keeping with the AMQP specification.
    - Renamed `AcceptMessage` to `MessageAccepted`.
    - Renamed `RejectMessage` to `MessageRejected` which now takes `condition` and `description` arguments rather than `message`.

- Added `errors.LinkDetach` exception as new subclass of `AMQPConnectionError` as a wrapped for data in a Link DETACH dispostition.
- Added `errors.LinkRedirect` as a specific subclass of `LinkDetach` to decode the specific redirect fields of a Link Redirect response.
- Added `errors.MessageAlreadySettled` exception for operations performed on a received message that has already returned a receipt dispostition.
- Added `errors.MessageReleased` exception.
- Added `errors.ErrorResponse` exception.
- A received Message can now be explicitly settled through a set of new functions on the message:

    - `Message.accept()`
    - `Message.reject(condition:str, description:str)`
    - `Message.release()`
    - `Message.modify(failed:bool, deliverable:bool, annotations:dict)`

- Added explicit `auto_complete` argument to `ReceiveClient` and `ReceiveClientAsync`. If `auto_complete` is set to `False` then all messages must be
  explicitly "accepted" or "rejected" by the user otherwise they will timeout and be released. The default is `True`, which is the exiting behaviour for each receive mechanism:

    - Received messages processed by callback (`ReceiveClient.receive_messages()`) will be automatically "accepted" if no explicit response has been set on completion of the callback.
    - Received messages processed by batch (`ReceiveClient.receive_message_batch()`) will by automatically "accepted" before being returned to the user.
    - Received messages processed by iterator (`ReceiveClient.receive_message_iter()`) will by automatically "accepted" if no explicit response has been set once the generator is incremented.

- Added new methods to clients and connections to allow to redirect to an alternative endpoint when a LinkRedirect exception is raised.
  The client redirect helper cannot be used for clients that use a shared connection - the clients must be closed before the connection can be redirected.
  New credentials must be supplied for the new endpoint. The new methods are:

    - `uamqp.Connection.redirect(redirect_info, auth)`
    - `uamqp.async.ConnectionAsync.redirect_async(redirect_info, auth)`
    - `uamqp.SendClient.redirect(redirect_info, auth)`
    - `uamqp.ReceiveClient.redirect(redirect_info, auth)`
    - `uamqp.async.SendClientAsync.redirect_async(redirect_info, auth)`
    - `uamqp.async.ReceiveClientAsync.redirect_async(redirect_info, auth)`

- Added `on_detach_received` argument to `Sender` and `Receiver` classes to pass in callback to run on Link DETACH.
- Removed automatic char encoding for strings of length 1, and added `types.AMQPChar` for explicit encoding.
- Bumped uAMQP C version to 1.2.5
- Bumped Azure C Shared Utility to 1.1.5
- Fixed memory leaks in MessageProperties, MessageHeader and message annotations.


0.1.0rc1 (2018-05-29)
+++++++++++++++++++++

- Fixed import error in async receiver.
- Exposed sender/receiver destroy function.
- Moved receiver.open on_message_received argument to constructor.
- Removed sasl module and moved internal classes into authentication module.
- Added encoding parameter everywhere where strings are encoded.
- Started documentation.
- Updated uAMQP-C to 1.2.4 and C Shared Utility to 1.1.4 (includes fix for issue #12).
- Fixed return type of MgmtOperation.execute - now returns ~uamqp.message.Message.
- Made AMQP connection/session/sender/receiver types in a client overridable.
- Added debug trace to management operations.
- Fixed error in management callback on failed operation.
- Default AMQP encoding of bytes is now a String type and a bytearray is a Binary type.
- Added AMQP Array type and fixed Long type range validation.
- Added `header` argument to Message and BatchMessage for setting a MessageHeader.
- Fixed MessageHeader attribute setters.


0.1.0b5 (2018-04-27)
++++++++++++++++++++

- Added Certifi as a depedency to make OpenSSL certs dynamic.
- Added `verify` option to authentication classes to allow setting custom certificate path (for Linux and OSX).


0.1.0b4 (2018-04-19)
++++++++++++++++++++

- Fixed memory leak in async receive.
- Removed close_on_done argument from client receive functions.
- Added receive iterator to synchronous client.
- Made async iter receive compatible with Python 3.5.


0.1.0b3 (2018-04-14)
++++++++++++++++++++

- Fixed SSL errors in manylinux wheels.
- Fixed message annoations attribute.
- Fixed bugs in batched messages and sending batched messages.
- Fixed conflicting receiver link ID.
- Fixed hanging receiver by removing queue max size in sync clients.
- Added support for sending messages with None and empty bodies.


0.1.0b2 (2018-04-06)
++++++++++++++++++++

- Added message send retry.
- Added timeouts and better error handling for management requests.
- Improved connection and auth error handling and error messages.
- Fixed message annotations type.
- SendClient.send_all_messages() now returns a list of message send statuses.
- Fixed OpenSSL platform being initialized multiple times.
- Fixed auto-refresh of SAS tokens.
- Altered `receive_batch` behaviour to return messages as soon as they're available.
- Parameter `batch_size` in `receive_batch` renamed to `max_batch_size`.
- Fixed message `application_properties` decode error.
- Removed MacOS dependency on OpenSSL and libuuid.


0.1.0b1 (2018-03-24)
++++++++++++++++++++

- Added management request support.
- Fixed message-less C operation ValueError.
- Store message metadata in Python rather than C.
- Refactored Send and Receive clients to create a generic parent AMQPClient.
- Fixed None receive timestamp bug.
- Removed async iterator queue due to instabilities - all callbacks are now synchronous.


0.1.0a3 (2018-03-19)
++++++++++++++++++++

- Added support for asynchronous message receive by iterator or batch.
- Removed synchronous receive iterator, and replaced with synchronous batch receive.
- Added sync and async context managers for Send and Receive Clients.
- Fixed token instability and added put token retry policy.
- Exposed Link ATTACH properties.
- A connection now has a single $cbs session that can be reused between clients.
- Added C debug trace logging to the Python logger ('uamqp.c_uamqp')


0.1.0a2 (2018-03-12)
++++++++++++++++++++

- Exposed OPEN performative properties for connection telemetry.
- Exposed setters for message.message_annotations and message.application_properties.
- Made adjustments to connection open and close to facilitate sharing a connection object between send/receive clients.
- Support for username/password embedded in connection URI.
- Clients can now optionally leave connection/session/link open for re-use.
- Updated build process and installation instructions.
- Various bug fixes to increase stability.


0.1.0a1 (2018-03-04)
++++++++++++++++++++

- Initial release