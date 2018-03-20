#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging

from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MgmtOperation:

    def __init__(self, session,
                 incoming_window=None,
                 outgoing_window=None,
                 handle_max=None):
        self._session = session
        self._mgmt_op = c_uamqp.create_management_operation(session._session)
        self.open_state = 

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

    def _management_open_complete(self, result):
        self.open_state = constants.MgmtOpenStatus(result)
    
    def _management_operation_error(self):
        pass
    
    def _management_operation_complete(self):
        pass

    def execute(self, operation, op_type, message):
        self._mgmt_op.execute(operation, op_type, None, message, self)

    def destroy(self):
        self._mgmt_op.destroy()