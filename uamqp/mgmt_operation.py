#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging

from uamqp import Session
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MgmtOperation:

    def __init__(self, connection, target=None):
        self.connection = connection
        self.session = Session(
            connection,
            incoming_window=constants.MAX_FRAME_SIZE_BYTES,
            outgoing_window=constants.MAX_FRAME_SIZE_BYTES)
        self.target = target if target else constants.MGMT_TARGET
        self._mgmt_op = c_uamqp.create_management_operation(self.session._session, self.target)
        self.open_state = None

        if incoming_window:
            self.incoming_window = incoming_window
        if outgoing_window:
            self.outgoing_window = outgoing_window
        if handle_max:
            self.handle_max = handle_max

    def _management_open_complete(self, result):
        self.open_state = constants.MgmtOpenStatus(result)
    
    def _management_operation_error(self):
        pass

    def execute(self, operation, op_type, message):
        response_message = None
        def _on_complete(operation_result, status_code, description, wrapped_message):
            result = constants.MgmtExecuteResult(operation_result)
            if result != constants.MgmtExecuteResult.Ok:
                _logger.error("Failed to complete mgmt operation.\nStatus code: {}\nMessage: {}".format(
                    status_code, description))
            response_message = wrapped_message

        self._mgmt_op.execute(operation, op_type, None, message, self)
        while not response_message:
            self.connection.work()

    def destroy(self):
        self._mgmt_op.destroy()