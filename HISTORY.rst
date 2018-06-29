.. :changelog:

Release History
===============

0.1.0rc2 (unreleased)
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

- **Breaking change** Combined the `AbandonMessage` and `DeferMessage` exceptions as `ModifyMessage` to be in keeping with the AMQP specification.
- Added `errors.LinkDetach` exception as new subclass of `AMQPConnectionError` as a wrapped for data in a Link DETACH dispostition.
- Added `errors.LinkRedirect` as a specific subclass of `LinkDetach` to decode the specific redirect fields of a Link Redirect response.
- Added `errors.MessageAlreadySettled` exception for operations performed on a received message that has already returned a receipt dispostition.
- Added `errors.ReleaseMessage` exception.
- Added `errors.ErrorResponse` exception.
- **Breaking change** The `errors.RejectMessage` now takes `condition` and `description` arguments rather than `message`.
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