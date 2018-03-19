#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp import receiver



_logger = logging.getLogger(__name__)


class MessageReceiverAsync(receiver.MessageReceiver):

    def __init__(self, session, source, target,
                 name=None,
                 receive_settle_mode=None,
                 max_message_size=None,
                 prefetch=None,
                 properties=None,
                 debug=False,
                 loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(MessageReceiverAsync, self).__init__(
            session, source, target,
            name=name,
            receive_settle_mode=receive_settle_mode,
            max_message_size=max_message_size,
            prefetch=prefetch,
            properties=properties,
            debug=debug)

    async def __aenter__(self):
        await self.open_async()
        return self

    async def __aexit__(self, *args):
        await self._destroy_async()

    async def _destroy_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._destroy))

    async def open_async(self, on_message_received):
        await self.loop.run_in_executor(None, functools.partial(self.open, on_message_received))

    async def close_async(self):
        await self.loop.run_in_executor(None, functools.partial(self.close))
