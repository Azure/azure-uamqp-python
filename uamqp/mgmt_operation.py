#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import uuid

#from uamqp.session import Session
from uamqp import constants
from uamqp import errors
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MgmtOperation:

    def __init__(self, session, target=None, status_code_field=b'statusCode', description_fields=b'statusDescription'):
        self.connection = session._connection
        # self.session = Session(
        #     connection,
        #     incoming_window=constants.MAX_FRAME_SIZE_BYTES,
        #     outgoing_window=constants.MAX_FRAME_SIZE_BYTES)
        self.target = target or constants.MGMT_TARGET
        self._responses = {}
        self._counter = c_uamqp.TickCounter()
        self._mgmt_op = c_uamqp.create_management_operation(session._session, self.target)
        self._mgmt_op.set_response_field_names(status_code_field, description_fields)
        self.open = None
        try:
            self._mgmt_op.open(self)
        except ValueError:
            self.mgmt_error = errors.AMQPConnectionError(
                "Unable to open management session. "
                "Please confirm URI namespace exists.")
        else:
            self.mgmt_error = None

    def _management_open_complete(self, result):
        self.open = constants.MgmtOpenStatus(result)
    
    def _management_operation_error(self):
        self.mgmt_error = ValueError("Management Operation error ocurred.")

    def execute(self, operation, op_type, message, timeout=0):
        start_time = self._counter.get_current_ms()
        operation_id = str(uuid.uuid4())
        self._responses[operation_id] = None

        def on_complete(operation_result, status_code, description, wrapped_message):
            result = constants.MgmtExecuteResult(operation_result)
            if result != constants.MgmtExecuteResult.Ok:
                _logger.error("Failed to complete mgmt operation.\nStatus code: {}\nMessage: {}".format(
                    status_code, description))
            self._responses[operation_id] = wrapped_message

        self._mgmt_op.execute(operation, op_type, None, message.get_message(), on_complete)
        while not self._responses[operation_id] and not self.mgmt_error:
            if timeout > 0:
                now = self._counter.get_current_ms()
                if (now - start_time) >= timeout:
                    raise TimeoutError("Failed to receive mgmt response in {}ms".format(timeout))
            self.connection.work()
        if self.mgmt_error:
            raise self.mgmt_error
        response = self._responses.pop(operation_id)
        return response

    def destroy(self):
        self._mgmt_op.destroy()