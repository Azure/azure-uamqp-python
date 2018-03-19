#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp import sender


_logger = logging.getLogger(__name__)


class MessageSenderAsync(sender.MessageSender):

    def __init__(self, session, source, target,
                 name=None,
                 send_settle_mode=None,
                 max_message_size=None,
                 link_credit=None,
                 properties=None,
                 debug=False,
                 loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(MessageSenderAsync, self).__init__(
            session, source, target,
            name=name,
            send_settle_mode=send_settle_mode,
            max_message_size=max_message_size,
            link_credit=link_credit,
            properties=properties,
            debug=debug)

    async def __aenter__(self):
        await self.open_async()
        return self

    async def __aexit__(self, *args):
        await self._destroy_async()

    async def _destroy_async(self):
        await self.loop.run_in_executor(None, functools.partial(self._destroy))

    async def open_async(self):
        await self.loop.run_in_executor(None, functools.partial(self.open))

    async def close_async(self):
        await self.loop.run_in_executor(None, functools.partial(self.close))
