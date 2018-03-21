#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp import session
from uamqp import constants
from uamqp.async.mgmt_operation_async import MgmtOperationAsync


_logger = logging.getLogger(__name__)


class SessionAsync(session.Session):

    def __init__(self, connection,
                 incoming_window=None,
                 outgoing_window=None,
                 handle_max=None,
                 loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(SessionAsync, self).__init__(
            connection,
            incoming_window=incoming_window,
            outgoing_window=outgoing_window,
            handle_max=handle_max)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.destroy_async()

    async def mgmt_request_async(self, message, operation, op_type=None, node=None, **kwargs):
        try:
            mgmt_link = self._mgmt_links[node]
        except KeyError:
            mgmt_link = MgmtOperationAsync(self, target=node, loop=self.loop, **kwargs)
            while not mgmt_link.open:
                await self._connection.work_async()
            if mgmt_link.open != constants.MgmtOpenStatus.Ok:
                raise ValueError("Failed to open mgmt link: {}".format(mgmt_link.open))
            self._mgmt_links[node] = mgmt_link
        op_type = op_type or b'empty'
        response = await mgmt_link.execute_async(operation, op_type, message)
        return response

    async def destroy_async(self):
        for node, link in self._mgmt_links.items():
           await link.destroy_async()
        await self.loop.run_in_executor(None, functools.partial(self._session.destroy))
