#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp import connection


_logger = logging.getLogger(__name__)


class ConnectionAsync(connection.Connection):

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 properties=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 debug=False,
                 loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(ConnectionAsync, self).__init__(
            hostname, sasl,
            container_id=container_id,
            max_frame_size=max_frame_size,
            channel_max=channel_max,
            idle_timeout=idle_timeout,
            properties=properties,
            remote_idle_timeout_empty_frame_send_ratio=remote_idle_timeout_empty_frame_send_ratio,
            debug=debug)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.destroy_async()

    async def work_async(self):
        await self.loop.run_in_executor(None, functools.partial(self.work))

    async def open_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._conn.open))

    async def destroy_async(self):
        if self.cbs:
            await self.auth.close_authenticator_async()
        await self.loop.run_in_executor(None, functools.partial(self._conn.destroy))
