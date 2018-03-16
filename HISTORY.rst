.. :changelog:

Release History
===============

0.1.0a3 (unreleased)
++++++++++++++++++++

- Added support for asynchronous message receive by iterator or batch.
- Removed synchronous receive iterator, and replaced with synchronous batch receive.
- Added sync and async context managers for Send and Receive Clients.
- Fixed token instability and added put token retry policy.
- Exposed Link ATTACH properties.


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