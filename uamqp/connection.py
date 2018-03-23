#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid
import threading

import uamqp
from uamqp import constants
from uamqp import c_uamqp
from uamqp import utils


_logger = logging.getLogger(__name__)


class Connection:

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 properties=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 debug=False):
        uamqp.initialize_platform()
        container_id = container_id if container_id else str(uuid.uuid4())
        self.hostname = hostname
        self.auth = sasl
        self.cbs = None
        self._conn = c_uamqp.create_connection(sasl.sasl_client.get_client(), hostname.encode('utf-8'), container_id.encode('utf-8'), self)
        self._conn.set_trace(debug)
        self._sessions = []
        self._lock = threading.Lock()

        if max_frame_size:
            self.max_frame_size = max_frame_size
        if channel_max:
            self.channel_max = channel_max
        if idle_timeout:
            self.idle_timeout = idle_timeout
        if properties:
            self.properties = properties
        if remote_idle_timeout_empty_frame_send_ratio:
            self._conn.remote_idle_timeout_empty_frame_send_ratio = remote_idle_timeout_empty_frame_send_ratio

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.destroy()

    def _state_changed(self, previous_state, new_state):
        try:
            _previous_state = c_uamqp.ConnectionState(previous_state)
        except ValueError:
            _previous_state = c_uamqp.ConnectionState.UNKNOWN
        try:
            _new_state = c_uamqp.ConnectionState(new_state)
        except ValueError:
            _new_state = c_uamqp.ConnectionState.UNKNOWN
        _logger.debug("Connection state changed from {} to {}".format(_previous_state, _new_state))

    def destroy(self):
        if self.cbs:
            self.auth.close_authenticator()
        self._conn.destroy()
        self.auth.close()
        uamqp.deinitialize_platform()

    def work(self):
        self._lock.acquire()
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
        self._conn.properties = utils.data_factory(value)

    @property
    def remote_max_frame_size(self):
        return self._conn.remote_max_frame_size
