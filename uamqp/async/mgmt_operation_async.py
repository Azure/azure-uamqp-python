#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import logging
import asyncio
import functools
import uuid

#from uamqp.session import Session
from uamqp.mgmt_operation import MgmtOperation
from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class MgmtOperationAsync(MgmtOperation):

    def __init__(self, session, target=None, status_code_field=b'statusCode', description_fields=b'statusDescription', loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(MgmtOperationAsync, self).__init__(
            session,
            target=target,
            status_code_field=status_code_field,
            description_fields=description_fields)

    async def execute_async(self, operation, op_type, message, timeout=0):
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
            await self.connection.work_async()
        if self.mgmt_error:
            raise self.mgmt_error
        response = self._responses.pop(operation_id)
        return response

    async def destroy_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._mgmt_op.destroy))