#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp import session


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

    async def destroy_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._session.destroy))
