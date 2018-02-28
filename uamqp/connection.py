#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid

from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class Connection:

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 debug=False):
        container_id = container_id if container_id else str(uuid.uuid4())
        self._conn = c_uamqp.create_connection(sasl.get_client(), hostname.encode('utf-8'), container_id.encode('utf-8'), self)
        self._conn.set_trace(debug)
        self._sessions = []

        if max_frame_size:
            self.max_frame_size = max_frame_size
        if channel_max:
            self.channel_max = channel_max
        if idle_timeout:
            self.idle_timeout = idle_timeout
        if remote_idle_timeout_empty_frame_send_ratio:
            self._conn.remote_idle_timeout_empty_frame_send_ratio = remote_idle_timeout_empty_frame_send_ratio

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._conn.destroy()

    def work(self):
        self._conn.do_work()

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
        self._conn.destroy()

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
    def remote_max_frame_size(self):
        return self._conn.remote_max_frame_size
