#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import asyncio
import logging
import time

import uamqp
from uamqp import c_uamqp, connection, errors, constants
from uamqp.utils import get_running_loop

_logger = logging.getLogger(__name__)


class ConnectionAsync(connection.Connection):
    """An Asynchronous AMQP Connection. A single Connection can have multiple
    Sessions, and can be shared between multiple Clients.

    :ivar max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :vartype max_frame_size: int
    :ivar channel_max: Maximum number of Session channels in the Connection.
    :vartype channel_max: int
    :ivar idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :vartype idle_timeout: int
    :ivar properties: Connection properties.
    :vartype properties: dict

    :param hostname: The hostname of the AMQP service with which to establish
     a connection.
    :type hostname: bytes or str
    :param sasl: Authentication for the connection. If none is provided SASL Annoymous
     authentication will be used.
    :type sasl: ~uamqp.authentication.common.AMQPAuth
    :param container_id: The name for the client, also known as the Container ID.
     If no name is provided, a random GUID will be used.
    :type container_id: str or bytes
    :param max_frame_size: Maximum AMQP frame size. Default is 63488 bytes.
    :type max_frame_size: int
    :param channel_max: Maximum number of Session channels in the Connection.
    :type channel_max: int
    :param idle_timeout: Timeout in milliseconds after which the Connection will close
     if there is no further activity.
    :type idle_timeout: int
    :param open_timeout: Timeout in milliseconds after which the Connection will close
     if it still can't get opened. If `None`, the Connection will keep trying to open until
     opened or meeting an error/end state. Default is `None`.
    :type open_timeout: int
    :param properties: Connection properties.
    :type properties: dict
    :param remote_idle_timeout_empty_frame_send_ratio: Ratio of empty frames to
     idle time for Connections with no activity. Value must be between
     0.0 and 1.0 inclusive. Default is 0.5.
    :type remote_idle_timeout_empty_frame_send_ratio: float
    :param debug: Whether to turn on network trace logs. If `True`, trace logs
     will be logged at INFO level. Default is `False`.
    :type debug: bool
    :param encoding: The encoding to use for parameters supplied as strings.
     Default is 'UTF-8'
    :type encoding: str
    :param loop: A user specified event loop.
    :type loop: ~asyncio.AbstractEventLoop
    """

    def __init__(self, hostname, sasl,
                 container_id=False,
                 max_frame_size=None,
                 channel_max=None,
                 idle_timeout=None,
                 properties=None,
                 remote_idle_timeout_empty_frame_send_ratio=None,
                 error_policy=None,
                 debug=False,
                 open_timeout=None,
                 encoding='UTF-8',
                 loop=None):
        self.loop = loop or get_running_loop()
        super(ConnectionAsync, self).__init__(
            hostname, sasl,
            container_id=container_id,
            max_frame_size=max_frame_size,
            channel_max=channel_max,
            idle_timeout=idle_timeout,
            properties=properties,
            remote_idle_timeout_empty_frame_send_ratio=remote_idle_timeout_empty_frame_send_ratio,
            error_policy=error_policy,
            debug=debug,
            open_timeout=open_timeout,
            encoding=encoding)
        self._async_lock = asyncio.Lock(loop=self.loop)

    async def __aenter__(self):
        """Open the Connection in an async context manager."""
        await self.open_async()
        return self

    async def __aexit__(self, *args):
        """Close the Connection when exiting an async context manager."""
        _logger.debug("Exiting connection %r context.", self.container_id)
        await self.destroy_async()
        _logger.debug("Finished exiting connection %r context.", self.container_id)

    async def _open_async(self, timeout=None):
        self._conn.open()
        connection_state = c_uamqp.ConnectionState(self._conn.get_state())
        timeout = timeout or self._open_timeout
        timeout_time = (time.time() * 1000 + timeout) if timeout else None
        while connection_state not in constants.CONNECTION_DONE_STATES:
            if timeout_time and time.time() * 1000 > timeout_time:
                raise errors.AMQPConnectionOpenTimeoutError('Connection open timeout.')
            await asyncio.sleep(0, loop=self.loop)
            self._conn.do_work()
            connection_state = c_uamqp.ConnectionState(self._conn.get_state())

        if connection_state != c_uamqp.ConnectionState.OPENED:
            raise errors.AMQPConnectionError('Fail to open connection.')

    async def _close_async(self):
        _logger.info("Shutting down connection %r.", self.container_id)
        self._closing = True
        if self._cbs:
            await self.auth.close_authenticator_async()
            self._cbs = None
        self._conn.destroy()
        self.auth.close()
        _logger.info("Connection shutdown complete %r.", self.container_id)

    async def open_async(self, timeout=None):
        try:
            await self.lock_async()
            await self._open_async(timeout)
        finally:
            self.release_async()

    async def lock_async(self, timeout=3.0):
        await asyncio.wait_for(self._async_lock.acquire(), timeout=timeout, loop=self.loop)

    def release_async(self):
        try:
            self._async_lock.release()
        except RuntimeError:
            pass
        except:
            _logger.debug("Got error when attempting to release async connection lock.")
            try:
                self._async_lock.release()
            except RuntimeError:
                pass
            raise

    async def work_async(self):
        """Perform a single Connection iteration asynchronously."""
        try:
            raise self._error
        except TypeError:
            pass
        except Exception as e:
            _logger.warning("%r", e)
            raise
        try:
            await self.lock_async()
            if self._closing:
                _logger.debug("Connection unlocked but shutting down.")
                return
            await asyncio.sleep(0, loop=self.loop)
            self._conn.do_work()
        except asyncio.TimeoutError:
            _logger.debug("Connection %r timed out while waiting for lock acquisition.", self.container_id)
        finally:
            await asyncio.sleep(0, loop=self.loop)
            self.release_async()

    async def sleep_async(self, seconds):
        """Lock the connection for a given number of seconds.

        :param seconds: Length of time to lock the connection.
        :type seconds: int
        """
        try:
            await self.lock_async()
            await asyncio.sleep(seconds, loop=self.loop)
        except asyncio.TimeoutError:
            _logger.debug("Connection %r timed out while waiting for lock acquisition.", self.container_id)
        finally:
            self.release_async()

    async def redirect_async(self, redirect_error, auth):
        """Redirect the connection to an alternative endpoint.
        :param redirect: The Link DETACH redirect details.
        :type redirect: ~uamqp.errors.LinkRedirect
        :param auth: Authentication credentials to the redirected endpoint.
        :type auth: ~uamqp.authentication.common.AMQPAuth
        """
        _logger.info("Redirecting connection %r.", self.container_id)
        try:
            await self.lock_async()
            if self.hostname == redirect_error.hostname:
                return
            if self._state != c_uamqp.ConnectionState.END:
                await self._close_async()
            self.hostname = redirect_error.hostname
            self.auth = auth
            self._conn = self._create_connection(auth)
            for setting, value in self._settings.items():
                setattr(self, setting, value)
            self._error = None
            self._closing = False
            await self._open_async()
        except asyncio.TimeoutError:
            _logger.debug("Connection %r timed out while waiting for lock acquisition.", self.container_id)
        finally:
            self.release_async()

    async def destroy_async(self):
        """Close the connection asynchronously, and close any associated
        CBS authentication session.
        """
        try:
            await self.lock_async()
            _logger.debug("Unlocked connection %r to close.", self.container_id)
            await self._close_async()
        except asyncio.TimeoutError:
            _logger.debug(
                "Connection %r timed out while waiting for lock acquisition on destroy. Destroying anyway.",
                self.container_id)
            await self._close_async()
        finally:
            self.release_async()
        uamqp._Platform.deinitialize()  # pylint: disable=protected-access
