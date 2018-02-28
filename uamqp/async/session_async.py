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

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.destroy_async()

    async def destroy_async(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, functools.partial(self._session.destroy))
