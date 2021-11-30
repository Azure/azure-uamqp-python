#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
import logging
import uuid
import time
from functools import partial

from .management_link import ManagementLink
from .message import Message
from .error import AMQPException

from .constants import (
    ManagementExecuteOperationResult
)

_LOGGER = logging.getLogger(__name__)


class ManagementOperation(object):
    def __init__(self, session, endpoint='$management', **kwargs):
        self.mgmt_link_open_status = None

        self._session = session
        self._connection = self._session._connection
        self._mgmt_link = self._session.create_request_response_link_pair(
            endpoint=endpoint,
            on_amqp_management_open_complete=self._on_amqp_management_open_complete,
            on_amqp_management_error=self._on_amqp_management_error,
            **kwargs
        )  # type: ManagementLink
        self._responses = {}
        self.mgmt_error = None

    def _on_amqp_management_open_complete(self, result):
        """Callback run when the send/receive links are open and ready
        to process messages.

        :param result: Whether the link opening was successful.
        :type result: int
        """
        self.mgmt_link_open_status = result

    def _on_amqp_management_error(self):
        """Callback run if an error occurs in the send/receive links."""
        # TODO: This probably shouldn't be ValueError
        self.mgmt_error = ValueError("Management Operation error occurred.")

    def _on_execute_operation_complete(
        self,
        operation_id,
        operation_result,
        status_code,
        status_description,
        raw_message,
        error=None
    ):
        _LOGGER.debug(
            "mgmt operation completed, operation id: %r; operation_result: %r; status_code: %r; "
            "status_description: %r, raw_message: %r, error: %r",
            operation_id,
            operation_result,
            status_code,
            status_description,
            raw_message,
            error
        )

        if operation_result in\
                (ManagementExecuteOperationResult.ERROR, ManagementExecuteOperationResult.INSTANCE_CLOSED):
            self.mgmt_error = error
            _LOGGER.error(
                "Failed to complete mgmt operation due to error: %r. The management request message is: %r",
                error, raw_message
            )
        else:
            self._responses[operation_id] = (status_code, status_description, raw_message)

    def execute(self, message, operation=None, operation_type=None, timeout=0):
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        self._responses[operation_id] = None
        self.mgmt_error = None

        self._mgmt_link.execute_operation(
            message,
            partial(self._on_execute_operation_complete, operation_id),
            timeout=timeout,
            operation=operation,
            type=operation_type
        )

        while not self._responses[operation_id] and not self.mgmt_error:
            if timeout > 0:
                now = time.time()
                if (now - start_time) >= timeout:
                    raise TimeoutError("Failed to receive mgmt response in {}ms".format(timeout))
            self._connection.listen()

        if self.mgmt_error:
            self._responses.pop(operation_id)
            raise self.mgmt_error

        response = self._responses.pop(operation_id)
        return response

    def open(self):
        self._mgmt_link.open()

    def close(self):
        self._mgmt_link.close()
