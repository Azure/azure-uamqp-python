#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid
import threading

import uamqp
from uamqp import c_uamqp
from uamqp import utils, errors


_logger = logging.getLogger(__name__)


class Connection:
    """An AMQP Connection. A single Connection can have multiple Sessions, and
    can be shared between multiple Clients.

    :ivar max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :vartype max_frame_size: int
    :ivar channel_max: Maximum number of Session channels in the Connection.
    :vartype channel_max: int
    :ivar idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :vartype idle_timeout: int
    :ivar properties: Connection properties.
    :vartype properties: dict

    :param hostname: The hostname of the AMQP service with which to establish
     a connection.
    :type hostname: bytes or str
    :param sasl: Authentication for the connection. If none is provided SASL Annoymous
     authentication will be used.
    :type sasl: ~uamqp.authentication.common.AMQPAuth
    :param container_id: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type container_id: str or bytes
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
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    """

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 properties=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 debug=False,
                 encoding='UTF-8'):
        uamqp._Platform.initialize()  # pylint: disable=protected-access
        self.container_id = container_id if container_id else str(uuid.uuid4())
        if isinstance(self.container_id, str):
            self.container_id = self.container_id.encode(encoding)
        self.hostname = hostname.encode(encoding) if isinstance(hostname, str) else hostname
        self.on_close_received = None
        self.auth = sasl
        self.cbs = None
        self._debug = debug
        self._conn = c_uamqp.create_connection(
            sasl.sasl_client.get_client(),
            self.hostname,
            self.container_id,
            self)
        self._conn.set_trace(self._debug)
        #self._conn.subscribe_to_close_event(self)
        self._sessions = []
        self._lock = threading.Lock()
        self._state = c_uamqp.ConnectionState.UNKNOWN
        self._encoding = encoding
        self._settings = {}
        self._error = None

        if max_frame_size:
            self._settings['max_frame_size'] = max_frame_size
            self.max_frame_size = max_frame_size
        if channel_max:
            self._settings['channel_max'] = channel_max
            self.channel_max = channel_max
        if idle_timeout:
            self._settings['idle_timeout'] = idle_timeout
            self.idle_timeout = idle_timeout
        if properties:
            self._settings['properties'] = properties
            self.properties = properties
        if remote_idle_timeout_empty_frame_send_ratio:
            self._conn.remote_idle_timeout_empty_frame_send_ratio = remote_idle_timeout_empty_frame_send_ratio

    def __enter__(self):
        """Open the Connection in a context manager."""
        return self

    def __exit__(self, *args):
        """Close the Connection when exiting a context manager."""
        self.destroy()

    def _close(self):
        if self.cbs:
            self.auth.close_authenticator()
            self.cbs = None
        self._conn.destroy()
        self.auth.close()

    def _close_received(self, error):
        """Callback called when a connection CLOSE frame is received.
        :param error: The error information from the close
         frame.
        :type error: ~uamqp.errors.ErrorResponse
        """
        _logger.info("In conneciton close received")
        condition = error.condition
        description = error.description
        info = error.info
        self._error = errors.ConnectionClose(condition, description, info)
        # if self.on_close_received:
        #     self.on_close_received(condition, description, info)

    def _state_changed(self, previous_state, new_state):
        """Callback called whenever the underlying Connection undergoes
        a change of state. This function wraps the states as Enums for logging
        purposes.
        :param previous_state: The previous Connection state.
        :type previous_state: int
        :param new_state: The new Connection state.
        :type new_state: int
        """
        try:
            _previous_state = c_uamqp.ConnectionState(previous_state)
        except ValueError:
            _previous_state = c_uamqp.ConnectionState.UNKNOWN
        try:
            _new_state = c_uamqp.ConnectionState(new_state)
        except ValueError:
            _new_state = c_uamqp.ConnectionState.UNKNOWN
        self._state = _new_state
        _logger.debug("Connection state changed from {} to {}".format(_previous_state, _new_state))

    def destroy(self):
        """Close the connection, and close any associated
        CBS authentication session.
        """
        self._close()
        uamqp._Platform.deinitialize()  # pylint: disable=protected-access

    def redirect(self, redirect_error, auth):
        """Redirect the connection to an alternative endpoint.
        :param redirect: The Link DETACH redirect details.
        :type redirect: ~uamqp.errors.LinkRedirect
        :param auth: Authentication credentials to the redirected endpoint.
        :type auth: ~uamqp.authentication.common.AMQPAuth
        """
        self._lock.acquire()
        try:
            if self.hostname == redirect_error.hostname:
                return
            if self._state != c_uamqp.ConnectionState.END:
                self._close()
            self.hostname = redirect_error.hostname
            self.auth = auth
            self._conn = c_uamqp.create_connection(
                self.auth.sasl_client.get_client(),
                self.hostname,
                self.container_id,
                self)
            self._conn.set_trace(self._debug)
            for setting, value in self._settings.items():
                setattr(self, setting, value)
        finally:
            self._lock.release()

    def work(self):
        """Perform a single Connection iteration."""
        self._lock.acquire()
        try:
            raise self._error
        except TypeError:
            pass
        self._conn.do_work()
        self._lock.release()

    @property
    def max_frame_size(self):
        return self._conn.max_frame_size

    @max_frame_size.setter
    def max_frame_size(self, value):
        self._conn.max_frame_size = int(value)

    @property
    def channel_max(self):
        return self._conn.channel_max

    @channel_max.setter
    def channel_max(self, value):
        self._conn.channel_max = int(value)

    @property
    def idle_timeout(self):
        return self._conn.idle_timeout

    @idle_timeout.setter
    def idle_timeout(self, value):
        self._conn.idle_timeout = int(value)

    @property
    def properties(self):
        return self._conn.properties

    @properties.setter
    def properties(self, value):
        if not isinstance(value, dict):
            raise TypeError("Connection properties must be a dictionary.")
        self._conn.properties = utils.data_factory(value, encoding=self._encoding)

    @property
    def remote_max_frame_size(self):
        return self._conn.remote_max_frame_size
