#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import asyncio
import functools

#from uamqp.session import Session
from uamqp.mgmt_operation import MgmtOperation
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MgmtOperationAsync(MgmtOperation):

    def __init__(self, session, target=None, loop=None, status_code_field=b'statusCode', description_fields=b'statusDescription'):
        self.loop = loop or asyncio.get_event_loop()
        self.connection = session._connection
        # self.session = Session(
        #     connection,
        #     incoming_window=constants.MAX_FRAME_SIZE_BYTES,
        #     outgoing_window=constants.MAX_FRAME_SIZE_BYTES)
        self.target = target or constants.MGMT_TARGET
        self._mgmt_op = c_uamqp.create_management_operation(session._session, self.target)
        self._mgmt_op.set_response_field_names(status_code_field, description_fields)
        self._mgmt_op.open(self)
        self._pending_ops = []
        self.open = None

    def _management_open_complete(self, result):
        self.open = constants.MgmtOpenStatus(result)
    
    def _management_operation_error(self):
        pass

    async def execute_async(self, operation, op_type, message):
        global response_message
        response_message = None
        def _on_complete(operation_result, status_code, description, wrapped_message):
            global response_message
            result = constants.MgmtExecuteResult(operation_result)
            if result != constants.MgmtExecuteResult.Ok:
                _logger.error("Failed to complete mgmt operation.\nStatus code: {}\nMessage: {}".format(
                    status_code, description))
            response_message = wrapped_message

        self._mgmt_op.execute(operation, op_type, None, message.get_message(), _on_complete)
        while not response_message:
            await self.connection.work_async()
        return response_message

    async def destroy_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._mgmt_op.destroy))