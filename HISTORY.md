# Release History

## 1.6.11 (2024-10-28)

-   Added support for python 3.13
-   Updated OpenSSL dependency to 3.0 LTS
-   Updated Cython dependency to 3.0.11
-   Updated Azure uAMQP C and Azure C Shared Utility dependencies

## 1.6.10 (2024-09-11)

-   Incorporate fixes from
    [PR](https://github.com/Azure/azure-sdk-for-cpp/pull/5917) to update
    vendor uamqp code.

## 1.6.9 (2024-03-20)

-   Incorporate fixes from
    [PR](https://github.com/Azure/azure-uamqp-c/commit/30865c9ccedaa32ddb036e87a8ebb52c3f18f695.patch)

## 1.6.8 (2024-01-29)

-   Incorporate fixes from
    [PR](https://github.com/Azure/azure-uamqp-c/pull/447)

## 1.6.7 (2024-01-17)

-   Fixes for CVE-2024-21646

## 1.6.6 (2023-11-16)

-   Added support for python 3.11

## 1.6.5 (2023-07-12)

-   Few more updates to submodules to support OpenSSL 3.0 compilation

## 1.6.4 (2023-02-09)

-   Updated OpenSSL dependency to 1.1.1t
-   Updated submodules to support OpenSSL 3.0 compilation
-   Removed dependency on six
-   Fixed a bug that caused the wrong port to selected for websockets
    when a port was not passed in

## 1.6.3 (2022-10-27)

-   Publish 3.11 wheels

## 1.6.2 (2022-10-27)

-   Added support for python 3.11
-   Updated OpenSSL dependency to 1.1.1q
-   Updated cython dependency to 0.29.32
-   Dropped support for manylinux2010
-   Using cibuildwheel to generate wheels

## 1.6.1 (2022-10-11)

-   Added support for handling of duplicate certificates in
    [azure-c-shared-utility]{.title-ref} dependency by using
    [CERT_STORE_ADD_REPLACE_EXISTING]{.title-ref} parameter in the
    [CertAddEncodedCertificateToStore]{.title-ref} function call.
    (azure-sdk-for-python issue #26034)

## 1.6.0 (2022-08-18)

This version and all future versions will require Python 3.7+, Python
3.6 is no longer supported.

-   Added [data]{.title-ref}, [value]{.title-ref},
    [sequence]{.title-ref} properties to [uamqp.Message]{.title-ref},
    which return the body if the body type corresponds.
-   Added [message_annotations]{.title-ref} property to
    [uamqp.Message]{.title-ref}, which is an alias for the
    [annotations]{.title-ref} instance variable.
-   Added [data]{.title-ref} property to
    [uamqp.BatchMessage]{.title-ref}, which returns the iterable body of
    the batch.
-   Added [ttl]{.title-ref} property to
    [uamqp.MessageHeader]{.title-ref}, which is an alias for the
    [time_to_live]{.title-ref} instance variable.

## 1.5.3 (2022-03-23)

-   Updated OpenSSL dependency to 1.1.1n for wheels of manylinux and
    macOS.

## 1.5.2 (2022-03-15)

-   Fixed bug that resulted in an error when deepcopying BatchMessage
    objects (azure-sdk-for-python issue #22529).

## 1.5.1 (2022-01-12)

-   Added back the support for Python 3.6.

## 1.5.0 (2022-01-05)

This version and all future versions will require Python 3.7+, Python
2.7 and Python 3.6 are no longer supported.

-   [SASTokenAuth]{.title-ref}, [JWTTokenAuth]{.title-ref},
    [SASTokenAsync]{.title-ref}, and [JWTTokenAsync]{.title-ref} now
    takes keyword argument [refresh_window]{.title-ref} to override
    default token refresh timing in constructors.
-   Fixed bug that [SendClientAsync]{.title-ref} might run into infinite
    loop while sending when it is shutdown unexpectedly.
-   Updated dependencies Azure uAMQP C @
    [2021-11-16](https://github.com/Azure/azure-uamqp-c/tree/259db533a66a8fa6e9ac61c39a9dae880224145f)
    and Azure C Shared Utility @
    [2021-11-15](https://github.com/Azure/azure-c-shared-utility/tree/735be16a943c2a9cbbddef0543f871f5bc0e27ab).
-   Fixed bug that the [keep_alive_thread]{.title-ref} of
    [AMQPClient]{.title-ref} should not keep program from exiting in the
    case of [AMQPClient]{.title-ref} not being closed properly.

## 1.4.3 (2021-10-06)

-   Added support for Python 3.10.

## 1.4.2 (2021-09-21)

-   Fixed memory leak in win32 socketio and tlsio (azure-sdk-for-python
    issue #19777).
-   Fixed memory leak in the process of converting AMQPValue into string
    (azure-sdk-for-python issue #19777).

## 1.4.1 (2021-06-28)

-   Fixed bug that JWTTokenAuth and JWTTokenAsync do not initialize
    token for token types other than b\'jwt\'.
-   Fixed bug that attibutes [creation_time]{.title-ref},
    [absolute_expiry_time]{.title-ref} and [group_sequence]{.title-ref}
    on [MessageProperties]{.title-ref} should be compatible with integer
    types on Python 2.7.

## 1.4.0 (2021-05-03)

This version and all future versions will require Python 2.7 or Python
3.6+, Python 3.5 is no longer supported.

-   Fixed memory leaks in the process of link attach where source and
    target cython objects are not properly deallocated
    (azure-sdk-for-python issue #15747).
-   Improved management operation callback not to parse description
    value of non AMQP_TYPE_STRING type as string (azure-sdk-for-python
    issue #18361).

## 1.3.0 (2021-04-05)

This version will be the last version to officially support Python 3.5,
future versions will require Python 2.7 or Python 3.6+.

-   Added support for AMQP Sequence as the body type of an amqp message.

-   Added new class [uamqp.MessageBodyType]{.title-ref} to represent the
    body type of an amqp message, including:

    > -   \`Data\`: The body consists of one or more data sections and
    >     each section contains opaque binary data.
    > -   \`Sequence\`: The body consists of one or more sequence
    >     sections and each section contains an arbitrary number of
    >     structured data elements.
    > -   \`Value\`: The body consists of one amqp-value section and the
    >     section contains a single AMQP value.

-   Added new parameters to the constructor of \`uamqp.Message\`:

    > -   [body_type]{.title-ref} which takes
    >     [uamqp.MessageBodyType]{.title-ref} to specify the body type
    >     of an amqp message.
    > -   [footer]{.title-ref} which takes a dict to set the footer of
    >     an amqp message.
    > -   [delivery_annotations]{.title-ref} which takes a dict to set
    >     the delivery annotations of an amqp message.

-   Added support for pickling [uamqp.Message]{.title-ref}.

-   Fixed bug that sending message of large size triggering segmentation
    fault when the underlying socket connection is lost.

-   Fixed bug in link flow control where link credit and delivery count
    should be calculated based on per message instead of per transfer
    frame.

## 1.2.15 (2021-03-02)

-   Added desired-capabilities for [SendClient(Async)]{.title-ref} and
    [MessageSender(Async)]{.title-ref} as part of the AMQP protocol.
-   Added types for AMQPShort and AMQPuShort for explicit handling of
    short and unsigned short encoding.

## 1.2.14 (2021-02-01)

-   Updated Azure uAMQP C and Azure C Shared Utility dependencies.
-   Fixed memory leak with SAS Token creation.

## 1.2.13 (2021-01-06)

-   Fixed bug in accessing [MessageProperties.user_id]{.title-ref}
    triggering segmentation fault when the underlying C bytes are NULL.
-   Fixed bug in [MessageProperties.user_id]{.title-ref} being limited
    to 8 bytes.
-   Fixed bug where connection establishment on macOS with Clang 12
    triggering unrecognized selector exception.
-   Fixed bug that macOS was unable to detect network error.
-   Fixed bug that [ReceiveClient]{.title-ref} and
    [ReceiveClientAsync]{.title-ref} receive messages during connection
    establishment.

## 1.2.12 (2020-10-09)

-   Updated cython dependency to 0.29.21.
-   Added support for Python 3.9.

## 1.2.11 (2020-10-01)

-   Updated tlsio_openssl module to send SNI when establishing tls
    connection (Thanks to milope).
-   Fixed bug where [Message.footer]{.title-ref} and
    [Message.delivery_annotation]{.title-ref} were not encoded into the
    outgoing payload.
-   Fixed bug where message sending timeout error didn\'t get raised
    out.

## 1.2.10 (2020-08-05)

-   Added parameter [shutdown_after_timeout]{.title-ref} to
    [ReceiveClient]{.title-ref} and [ReceiveClientAsync]{.title-ref}
    which gives control over whether to shutdown receiver after timeout.

## 1.2.9 (2020-07-06)

-   Added method [MessageReceiver.reset_link_credit]{.title-ref} which
    is responsible for resetting current available link credit on the
    receiver link and send update to the sender.

## 1.2.8 (2020-05-19)

-   Fix to initialize delivery_count header at 0 instead of None
    (azure-sdk-for-python issue #9708)
-   Added info fields to rejected delivery disposition.

## 1.2.7 (2020-05-04)

-   Fixed bug in setting certificate of tlsio on MacOS
    (azure-sdk-for-python issue #7201).
-   Fixed seg fault in logging network tracing on MacOS (PR#147, Thanks
    to malthe).
-   Fixed typos in log messages (PR#146, Thanks to bluca).
-   Improved reproducibility of the generated c_uamqp.c file (PR#144,
    Thanks to bluca).

## 1.2.6 (2020-02-13)

-   Fixed seg fault in tearing down a failed link with unsent pending
    messages.

## 1.2.5 (2019-12-10)

-   Fixed garbage collection of C objects to prevent crashing on
    uncontrolled shutdown.
-   Fixed missing event loop references passed into asyncio functions.
-   Fixed bug in noneffective flow control when large messages are
    received.
-   Demote link redirect logging from warning to info.

## 1.2.4 (2019-12-02)

-   Fixed bug in calculating send timeout.
-   Removed [ThreadPoolExecutor]{.title-ref} in
    [ConnectionAsync]{.title-ref}.
-   Added support for Python 3.8

## 1.2.3 (2019-10-07)

-   Fixed bug in dropping received messages at the moment when the
    connection just started working.
-   Fixed bug where underlying io type wasn\'t set to WebSocket when
    http_proxy was applied (PR#92, Thanks to skoop22).
-   Fixed bug in noneffective timeout when sending messages.
-   Added desired-capabilities for [ReceiveClient(Async)]{.title-ref}
    and [MessageReceiver(Async)]{.title-ref} as part of the AMQP
    protocol.
-   Added delivery-tag to [Message]{.title-ref} (azure-sdk-for-python
    issue #7336).
-   Added method [work]{.title-ref} to [MessageReceiver]{.title-ref} and
    [work_async]{.title-ref} to [MessageReceiverAsync]{.title-ref}
    responsible for updating link status.

## 1.2.2 (2019-07-02)

-   Made bug fix in asyncio.get_event_loop backwards-compatible for now
    by just printing a warning rather than raising an error. In the next
    major version bump we can disable entirely.

## 1.2.1 (2019-06-20)

-   Updated the implementation of [update_token()]{.title-ref} in
    [JWTTokenAuth]{.title-ref} and [JWTTokenAsync]{.title-ref} (issue
    #80).

## 1.2.0 (2019-04-16)

-   Fixed bug in batched messages missing application_properties
    (azure-event-hubs-python issue #97).
-   Fixed bug in datetime object parsing (issue #63).
-   Fixed bug in unexposed send/receive settle modes.
-   Fixed bug where retried messages were not added back to the send
    queue.
-   Fixed bug in using asyncio.get_event_loop.
-   Added type objects for AMQP Byte and uBytes types.
-   Added async locking around pending messages queue (PR#54, Thanks to
    zach-b)
-   Added WebSocket(AMQP over WebSocket) support (azure-sdk-for-python
    issue #5318).
-   Added new token class [JWTTokenAuth]{.title-ref} and
    [JWTTokenAsync]{.title-ref} to support OAuth.

## 1.1.0 (2018-11-12)

-   Support for Python 2.7 (\>\_\<)/

    > -   Where ever a [TimeoutError]{.title-ref} is raised in Python
    >     3.x, this will be replaced with a new
    >     \~uamqp.errors.ClientTimeout exception in Python 2.7.
    > -   A Python 2 [str]{.title-ref} object will be treated as
    >     [bytes]{.title-ref} in Python 3 and a Python 2
    >     [unicode]{.title-ref} object will be treated like a Python 3
    >     [str]{.title-ref}.
    > -   Added uamqp.compat module for handling Py 2 vs 3 imports and
    >     types (PR#46, Thanks to maxkrivich).

-   AMQP encoding of an integer type will now automatically failover
    into a Long type or a double type if the value is too large.

-   Improved support for promptly detecting invalid ATTACH handles and
    raising the appropriate error.

-   Added types for AMQPDescribed, AMQPInt and AMQPuInt for explicit
    handling of int and unsigned int encoding.

-   Added new error [errors.AMQPClientShutdown]{.title-ref} as a wrapper
    for [KeyboardInterrupt]{.title-ref} to better handle interrupt
    handling.

-   Added better handling of keyboard interrupts during C callbacks to
    better facilitate clean client shutdown.

-   Added additional handling of keyboard interrupt at the C level to
    clean up annoying warnings.

-   Added classmethod [Message.decode_from_bytes]{.title-ref} to create
    a message from AMQP wire-encoded data.

-   Added [Message.encode_message]{.title-ref} method to retrieve the
    AMQP wire-encoded byte representation of the current message.

-   Fixed behaviour of [Message.get_message_encoded_size()]{.title-ref}
    to return accurate size.

-   Added new optional [callback]{.title-ref} argument to
    [client.mgmt_request]{.title-ref} to allow for custom handling of
    different status codes.

-   Added new client methods [auth_complete()]{.title-ref} and
    [client_ready()]{.title-ref} to allow for more fine-tuned monitoring
    or the client opening stages.

-   Client message handler is now a public attribute
    [client.message_handler]{.title-ref}
    ([SendClient.\_message_sender]{.title-ref} and
    [ReceiveClient.\_message_receiver]{.title-ref} are now deprecated).

-   Added automatic encoding of [datetime.datetime]{.title-ref} objects
    into AMQP timestamp.

-   Better support for Source filters with optional
    [descriptor]{.title-ref} argument in
    [Source.set_filter()]{.title-ref} and new
    [Source.get_filter()]{.title-ref} method.

-   Fixed Session settings not being passed to CBS session.

-   Added support for a callback on receipt on a Link ATTACH frame. Can
    be supplied to a client through the [on_attach]{.title-ref} keyword
    argument.

-   Removed unsued message.SequenceBody class.

-   Exposed BatchMessage.size_offset property for batch size
    customization.

## 1.0.3 (2018-09-14)

-   Reduced CPU load during idle receive.
-   Updated Azure uAMQP C and Azure C Shared Utility dependencies.

## 1.0.2 (2018-09-05)

-   Fixed additional bugs in setting MessageProperties as string or
    bytes.
-   Removed auth locking to prevent locking issues on keyboard
    interrupt.

## 1.0.1 (2018-08-29)

-   Added some more checks in place to prevent lock hanging on a
    keybaord interrupt.
-   Fixed bug in setting MessageProperties.subject as string or bytes.
-   [uamqp.send_message]{.title-ref} now returns a list of
    [uamqp.constants.MessageState]{.title-ref} to indicate the success
    of each message sent.

## 1.0.0 (2018-08-20)

-   API settled.

-   **Behaviour change** When a SendClient or SendClientAsync is
    shutdown, any remaining pending messages (that is messages in the
    states [WaitingToBeSent]{.title-ref} and
    [WaitingForSendAck]{.title-ref}) will no longer be cleared, but can
    be retrieved from a new attribute
    [SendClient.pending_messages]{.title-ref} in order to be
    re-processed as needed.

-   **Behaviour change** The function
    [SendClient.queue_message]{.title-ref} now allows for queueing
    multiple messages at once by simply passing in additional message
    instances:

    > -   [send_client.queue_message(my_message)]{.title-ref}
    > -   [send_client.queue_message(message_1, message_2,
    >     message_3)]{.title-ref}
    > -   [send_client.queue_message(\*my_message_list)]{.title-ref}

-   An authentication object will now raise a [ValueError]{.title-ref}
    if one attempts to use it for more than one connection.

-   Renamed internal [\_async]{.title-ref} module to non-private
    [async_ops]{.title-ref} to allow for docs generation.

-   Reformatted logging for better performance.

-   Added additional logging.

## 0.2.1 (2018-08-06)

-   Fixed potential crashing in bindings for amqpvalue.
-   Fixed bindings fault in cbs PUT token complete callback.
-   Updated uAMQP-C.
-   Added additional auth and connection locking for thread/async
    safety.
-   Increased INFO level logging.
-   Removed platform deinitialization until it can be improved.
-   Added handling for a connection reaching a client-caused error
    state.

## 0.2.0 (2018-07-25)

-   **Breaking change** [MessageSender.send_async]{.title-ref} has been
    renamed to [MessageSender.send]{.title-ref}, and
    [MessageSenderAsync.send_async]{.title-ref} is now a coroutine.

-   **Breaking change** Removed [detach_received]{.title-ref} callback
    argument from MessageSender, MessageReceiver, MessageSenderAsync,
    and MessageReceiverAsync in favour of new [error_policy]{.title-ref}
    argument.

-   Added ErrorPolicy class to determine how the client should respond
    to both generic AMQP errors and custom or vendor-specific errors. A
    default policy will be used, but a custom policy can be added to any
    client by using a new [error_policy]{.title-ref} argument. Value
    must be either an instance or subclass of ErrorPolicy.

    > -   The [error_policy]{.title-ref} argument has also been added to
    >     MessageSender, MessageReceiver, Connection, and their async
    >     counterparts to allow for handling of link DETACH and
    >     connection CLOSE events.
    > -   The error policy passed to a SendClient determines the number
    >     of message send retry attempts. This replaces the previous
    >     [constants.MESSAGE_SEND_RETRIES]{.title-ref} value which is
    >     now deprecated.
    > -   Added new ErrorAction object to determine how a client should
    >     respond to an error. It has three properties:
    >     [retry]{.title-ref} (a boolean to determine whether the error
    >     is retryable), [backoff]{.title-ref} (an integer to determine
    >     how long the client should wait before retrying, default is 0)
    >     and [increment_retries]{.title-ref} (a boolean to determine
    >     whether the error should count against the maximum retry
    >     attempts, default is [True]{.title-ref}). Currently
    >     [backoff]{.title-ref} and [increment_retries]{.title-ref} are
    >     only considered for message send failures.
    > -   Added [VendorConnectionClose]{.title-ref} and
    >     [VendorLinkDetach]{.title-ref} exceptions for non-standard
    >     (unrecognized) connection/link errors.

-   Added support for HTTP proxy configuration.

-   Added support for running async clients synchronously.

-   Added keep-alive support for connection - this is a background
    thread for a synchronous client, and a background async function for
    an async client. The keep-alive feature is disabled by default, to
    enable, set the [keep_alive_interval]{.title-ref} argument on the
    client to an integer representing the number of seconds between
    connection pings.

-   Added support for catching a Connection CLOSE event.

-   Added support for [Connection.sleep]{.title-ref} and
    [ConnectionAsync.sleep_async]{.title-ref} to pause the connection.

-   Added support for surfacing message disposition delivery-state (with
    error information).

-   Added [constants.ErrorCodes]{.title-ref} enum to map standard AMQP
    error conditions. This replaces the previous
    [constants.ERROR_CONNECTION_REDIRECT]{.title-ref} and
    [constants.ERROR_LINK_REDIRECT]{.title-ref} which are now both
    deprecated.

-   Added new super error [AMQPError]{.title-ref} from which all
    exceptions inherit.

-   Added new [MessageHandlerError]{.title-ref} exception, a subclass of
    [AMQPConnectionError]{.title-ref}, for Senders/Receivers that enter
    an indeterminate error state.

-   [MessageException]{.title-ref} is now a subclass of
    [MessageResponse]{.title-ref}.

-   Added [ClientMessageError]{.title-ref} exception, a subclass of
    [MessageException]{.title-ref} for send errors raised client-side.

-   Catching Link DETACH event will now work regardless of whether
    service returns delivery-state.

-   Fixed bug where received messages attempting to settle on a detached
    link crashed the client.

-   Fixed bug in amqp C DescribedValue.

-   Fixed bug where client crashed on deallocating failed management
    operation.

## 0.1.1 (2018-07-14)

-   Removed circular dependency in Python 3.4 with types.py/utils.py
-   When a header properties is not set, returns [None]{.title-ref}
    rather than raising ValueError.
-   Fixed bug in receiving messages with application properties.

## 0.1.0 (2018-07-05)

-   Fixed bug in error handling for CBS auth to invalid hostname.
-   Changed C error logging to debug level.
-   Bumped uAMQP C version to 1.2.7
-   Fixed memory leaks and deallocation bugs with Properties and
    Annotations.

## 0.1.0rc2 (2018-07-02)

-   **Breaking change** Submodule [async]{.title-ref} has been renamed
    to the internal [\_async]{.title-ref}. All asynchronous classes in
    the submodule can now be accessed from uamqp or uamqp.authentication
    directly.

-   **Breaking change** Anything returned by a callback supplied to
    receive messages will now be ignored.

-   **Breaking change** Changed message state enum values:

    > -   [Complete -\> SendComplete]{.title-ref}
    > -   [Failed -\> SendFailed]{.title-ref}
    > -   [WaitingForAck -\> WaitingForSendAck]{.title-ref}

-   Added new message state enum values:

    > -   [ReceivedUnsettled]{.title-ref}
    > -   [ReceivedSettled]{.title-ref}

-   **Breaking change** Changes to message settlement exceptions:

    > -   Combined the [AbandonMessage]{.title-ref} and
    >     [DeferMessage]{.title-ref} exceptions as
    >     [MessageModified]{.title-ref} to be in keeping with the AMQP
    >     specification.
    > -   Renamed [AcceptMessage]{.title-ref} to
    >     [MessageAccepted]{.title-ref}.
    > -   Renamed [RejectMessage]{.title-ref} to
    >     [MessageRejected]{.title-ref} which now takes
    >     [condition]{.title-ref} and [description]{.title-ref}
    >     arguments rather than [message]{.title-ref}.

-   Added [errors.LinkDetach]{.title-ref} exception as new subclass of
    [AMQPConnectionError]{.title-ref} as a wrapped for data in a Link
    DETACH dispostition.

-   Added [errors.LinkRedirect]{.title-ref} as a specific subclass of
    [LinkDetach]{.title-ref} to decode the specific redirect fields of a
    Link Redirect response.

-   Added [errors.MessageAlreadySettled]{.title-ref} exception for
    operations performed on a received message that has already returned
    a receipt dispostition.

-   Added [errors.MessageReleased]{.title-ref} exception.

-   Added [errors.ErrorResponse]{.title-ref} exception.

-   A received Message can now be explicitly settled through a set of
    new functions on the message:

    > -   [Message.accept()]{.title-ref}
    > -   [Message.reject(condition:str, description:str)]{.title-ref}
    > -   [Message.release()]{.title-ref}
    > -   [Message.modify(failed:bool, deliverable:bool,
    >     annotations:dict)]{.title-ref}

-   Added explicit [auto_complete]{.title-ref} argument to
    [ReceiveClient]{.title-ref} and [ReceiveClientAsync]{.title-ref}. If
    [auto_complete]{.title-ref} is set to [False]{.title-ref} then all
    messages must be explicitly \"accepted\" or \"rejected\" by the user
    otherwise they will timeout and be released. The default is
    [True]{.title-ref}, which is the exiting behaviour for each receive
    mechanism:

    > -   Received messages processed by callback
    >     ([ReceiveClient.receive_messages()]{.title-ref}) will be
    >     automatically \"accepted\" if no explicit response has been
    >     set on completion of the callback.
    > -   Received messages processed by batch
    >     ([ReceiveClient.receive_message_batch()]{.title-ref}) will by
    >     automatically \"accepted\" before being returned to the user.
    > -   Received messages processed by iterator
    >     ([ReceiveClient.receive_message_iter()]{.title-ref}) will by
    >     automatically \"accepted\" if no explicit response has been
    >     set once the generator is incremented.

-   Added new methods to clients and connections to allow to redirect to
    an alternative endpoint when a LinkRedirect exception is raised. The
    client redirect helper cannot be used for clients that use a shared
    connection - the clients must be closed before the connection can be
    redirected. New credentials must be supplied for the new endpoint.
    The new methods are:

    > -   [uamqp.Connection.redirect(redirect_info, auth)]{.title-ref}
    > -   [uamqp.async.ConnectionAsync.redirect_async(redirect_info,
    >     auth)]{.title-ref}
    > -   [uamqp.SendClient.redirect(redirect_info, auth)]{.title-ref}
    > -   [uamqp.ReceiveClient.redirect(redirect_info,
    >     auth)]{.title-ref}
    > -   [uamqp.async.SendClientAsync.redirect_async(redirect_info,
    >     auth)]{.title-ref}
    > -   [uamqp.async.ReceiveClientAsync.redirect_async(redirect_info,
    >     auth)]{.title-ref}

-   Added [on_detach_received]{.title-ref} argument to
    [Sender]{.title-ref} and [Receiver]{.title-ref} classes to pass in
    callback to run on Link DETACH.

-   Removed automatic char encoding for strings of length 1, and added
    [types.AMQPChar]{.title-ref} for explicit encoding.

-   Bumped uAMQP C version to 1.2.5

-   Bumped Azure C Shared Utility to 1.1.5

-   Fixed memory leaks in MessageProperties, MessageHeader and message
    annotations.

## 0.1.0rc1 (2018-05-29)

-   Fixed import error in async receiver.
-   Exposed sender/receiver destroy function.
-   Moved receiver.open on_message_received argument to constructor.
-   Removed sasl module and moved internal classes into authentication
    module.
-   Added encoding parameter everywhere where strings are encoded.
-   Started documentation.
-   Updated uAMQP-C to 1.2.4 and C Shared Utility to 1.1.4 (includes fix
    for issue #12).
-   Fixed return type of MgmtOperation.execute - now returns
    \~uamqp.message.Message.
-   Made AMQP connection/session/sender/receiver types in a client
    overridable.
-   Added debug trace to management operations.
-   Fixed error in management callback on failed operation.
-   Default AMQP encoding of bytes is now a String type and a bytearray
    is a Binary type.
-   Added AMQP Array type and fixed Long type range validation.
-   Added [header]{.title-ref} argument to Message and BatchMessage for
    setting a MessageHeader.
-   Fixed MessageHeader attribute setters.

## 0.1.0b5 (2018-04-27)

-   Added Certifi as a depedency to make OpenSSL certs dynamic.
-   Added [verify]{.title-ref} option to authentication classes to allow
    setting custom certificate path (for Linux and OSX).

## 0.1.0b4 (2018-04-19)

-   Fixed memory leak in async receive.
-   Removed close_on_done argument from client receive functions.
-   Added receive iterator to synchronous client.
-   Made async iter receive compatible with Python 3.5.

## 0.1.0b3 (2018-04-14)

-   Fixed SSL errors in manylinux wheels.
-   Fixed message annoations attribute.
-   Fixed bugs in batched messages and sending batched messages.
-   Fixed conflicting receiver link ID.
-   Fixed hanging receiver by removing queue max size in sync clients.
-   Added support for sending messages with None and empty bodies.

## 0.1.0b2 (2018-04-06)

-   Added message send retry.
-   Added timeouts and better error handling for management requests.
-   Improved connection and auth error handling and error messages.
-   Fixed message annotations type.
-   SendClient.send_all_messages() now returns a list of message send
    statuses.
-   Fixed OpenSSL platform being initialized multiple times.
-   Fixed auto-refresh of SAS tokens.
-   Altered [receive_batch]{.title-ref} behaviour to return messages as
    soon as they\'re available.
-   Parameter [batch_size]{.title-ref} in [receive_batch]{.title-ref}
    renamed to [max_batch_size]{.title-ref}.
-   Fixed message [application_properties]{.title-ref} decode error.
-   Removed MacOS dependency on OpenSSL and libuuid.

## 0.1.0b1 (2018-03-24)

-   Added management request support.
-   Fixed message-less C operation ValueError.
-   Store message metadata in Python rather than C.
-   Refactored Send and Receive clients to create a generic parent
    AMQPClient.
-   Fixed None receive timestamp bug.
-   Removed async iterator queue due to instabilities - all callbacks
    are now synchronous.

## 0.1.0a3 (2018-03-19)

-   Added support for asynchronous message receive by iterator or batch.
-   Removed synchronous receive iterator, and replaced with synchronous
    batch receive.
-   Added sync and async context managers for Send and Receive Clients.
-   Fixed token instability and added put token retry policy.
-   Exposed Link ATTACH properties.
-   A connection now has a single \$cbs session that can be reused
    between clients.
-   Added C debug trace logging to the Python logger (\'uamqp.c_uamqp\')

## 0.1.0a2 (2018-03-12)

-   Exposed OPEN performative properties for connection telemetry.
-   Exposed setters for message.message_annotations and
    message.application_properties.
-   Made adjustments to connection open and close to facilitate sharing
    a connection object between send/receive clients.
-   Support for username/password embedded in connection URI.
-   Clients can now optionally leave connection/session/link open for
    re-use.
-   Updated build process and installation instructions.
-   Various bug fixes to increase stability.

## 0.1.0a1 (2018-03-04)

-   Initial release
