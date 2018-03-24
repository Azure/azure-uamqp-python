#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging

from uamqp import c_uamqp
from uamqp import mgmt_operation
from uamqp import constants


_logger = logging.getLogger(__name__)


class Session:

    def __init__(self, connection,
                 incoming_window=None,
                 outgoing_window=None,
                 handle_max=None):
        self._connection = connection
        self._conn = connection._conn
        self._session = c_uamqp.create_session(self._conn)
        self._mgmt_links = {}

        if incoming_window:
            self.incoming_window = incoming_window
        if outgoing_window:
            self.outgoing_window = outgoing_window
        if handle_max:
            self.handle_max = handle_max

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._session.destroy()

    def mgmt_request(self, message, operation, op_type=None, node=None, **kwargs):
        try:
            mgmt_link = self._mgmt_links[node]
        except KeyError:
            mgmt_link = mgmt_operation.MgmtOperation(self, target=node, **kwargs)
            while not mgmt_link.open:
                self._connection.work()
            if mgmt_link.open != constants.MgmtOpenStatus.Ok:
                raise ValueError("Failed to open mgmt link: {}".format(mgmt_link.open))
            self._mgmt_links[node] = mgmt_link
        op_type = op_type or b'empty'
        response = mgmt_link.execute(operation, op_type, message)
        return response

    def destroy(self):
        for node, link in self._mgmt_links.items():
           link.destroy()
        self._session.destroy()

    @property
    def incoming_window(self):
        return self._session.incoming_window

    @incoming_window.setter
    def incoming_window(self, value):
        self._session.incoming_window = int(value)

    @property
    def outgoing_window(self):
        return self._session.outgoing_window

    @outgoing_window.setter
    def outgoing_window(self, value):
        self._session.outgoing_window = int(value)

    @property
    def handle_max(self):
        return self._session.handle_max

    @handle_max.setter
    def handle_max(self, value):
        self._session.handle_max = int(value)
