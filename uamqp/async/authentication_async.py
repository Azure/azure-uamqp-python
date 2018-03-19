#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import functools

from uamqp.async import SessionAsync
from uamqp import constants
from uamqp import authentication
from uamqp import errors
from uamqp import c_uamqp

_logger = logging.getLogger(__name__)


class CBSAsyncAuthMixin(authentication.CBSAuthMixin):

    async def create_authenticator_async(self, connection, debug=False, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._session = SessionAsync(
            connection,
            incoming_window=constants.MAX_FRAME_SIZE_BYTES,
            outgoing_window=constants.MAX_FRAME_SIZE_BYTES,
            loop=self.loop)
        self._cbs_auth = c_uamqp.CBSTokenAuth(
            self.audience,
            self.token_type,
            self.token,
            self.expiry,
            self._session._session,
            self.timeout)
        self._cbs_auth.set_trace(debug)
        return self._cbs_auth

    async def close_authenticator_async(self):
        await self.loop.run_in_executor(None, functools.partial(self.close_authenticator))
        await self._session.destroy_async()

    async def handle_token_async(self):
        timeout = False
        in_progress = False
        auth_status = await self.loop.run_in_executor(None, functools.partial(self._cbs_auth.get_status))
        auth_status = constants.CBSAuthStatus(auth_status)
        if auth_status == constants.CBSAuthStatus.Failure:
            if self.retries >= self._retry_policy.retries:
                _logger.warning("Authentication Put-Token failed. Retries exhausted.")
                raise errors.TokenAuthFailure(*self._cbs_auth.get_failure_info())
            else:
                _logger.info("Authentication Put-Token failed. Retrying.")
                self.retries += 1
                await asyncio.sleep(self._retry_policy.backoff)
                await self.loop.run_in_executor(None, functools.partial(self._cbs_auth.authenticate))
                in_progress = True
        elif auth_status == constants.CBSAuthStatus.Expired:
            raise errors.TokenExpired("CBS Authentication Expired.")
        elif auth_status == constants.CBSAuthStatus.Timeout:
            timeout = True
        elif auth_status == constants.CBSAuthStatus.InProgress:
            in_progress = True
        elif auth_status == constants.CBSAuthStatus.RefreshRequired:
            await self.loop.run_in_executor(None, functools.partial(self._cbs_auth.refresh, None))
        elif auth_status == constants.CBSAuthStatus.Idle:
            await self.loop.run_in_executor(None, functools.partial(self._cbs_auth.authenticate))
            in_progress = True
        elif auth_status == constants.CBSAuthStatus.Ok:
            if self._refresh_token:
                try:
                    await self.loop.run_in_executor(None, functools.partial(self._cbs_auth.refresh, self._refresh_token))
                finally:
                    self._refresh_token = None
        else:
            raise ValueError("Invalid auth state.")
        return timeout, in_progress


class SASTokenAsync(authentication.SASTokenAuth, CBSAsyncAuthMixin):
    pass