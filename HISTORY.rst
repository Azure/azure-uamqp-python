.. :changelog:

Release History
===============

0.1.0b1 (unreleased)
++++++++++++++++++++

- Added management request support.
- Fixed message-less C operation ValueError.
- Store message metadata in Python rather than C.
- Refactored Send and Receive clients to create a generic parent AMQPClient.


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