import sys
import pytest

import asyncio
from uamqp.async_ops.mgmt_operation_async import MgmtOperationAsync
from uamqp.async_ops.receiver_async import MessageReceiverAsync
from uamqp.authentication.cbs_auth_async import CBSAsyncAuthMixin
from uamqp.async_ops.sender_async import MessageSenderAsync
from uamqp.async_ops.client_async import (
    AMQPClientAsync,
    SendClientAsync,
    ReceiveClientAsync,
    ConnectionAsync,
)

@pytest.mark.asyncio
@pytest.mark.skipif(sys.version_info < (3, 10), reason="raise error if loop passed in >=3.10")
async def test_error_loop_arg_async():
    with pytest.raises(ValueError) as e:
        AMQPClientAsync("fake_addr", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e
    client_async = AMQPClientAsync("sb://resourcename.servicebus.windows.net/")
    assert len(client_async._internal_kwargs) == 0  # pylint:disable=protected-access

    with pytest.raises(ValueError) as e:
        SendClientAsync("fake_addr", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e
    client_async = SendClientAsync("sb://resourcename.servicebus.windows.net/")
    assert len(client_async._internal_kwargs) == 0  # pylint:disable=protected-access

    with pytest.raises(ValueError) as e:
        ReceiveClientAsync("fake_addr", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e
    client_async = ReceiveClientAsync("sb://resourcename.servicebus.windows.net/")
    assert len(client_async._internal_kwargs) == 0  # pylint:disable=protected-access

    with pytest.raises(ValueError) as e:
        ConnectionAsync("fake_addr", sasl='fake_sasl', loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e

    with pytest.raises(ValueError) as e:
        MgmtOperationAsync("fake_addr", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e

    with pytest.raises(ValueError) as e:
        MessageReceiverAsync("fake_addr", "session", "target", "on_message_received", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e

    with pytest.raises(ValueError) as e:
        MessageSenderAsync("fake_addr", "source", "target", loop=asyncio.get_event_loop())
        assert "no longer supports loop" in e

    async def auth_async_loop():
        auth_async = CBSAsyncAuthMixin()
        with pytest.raises(ValueError) as e:
            await auth_async.create_authenticator_async("fake_conn", loop=asyncio.get_event_loop())
            assert "no longer supports loop" in e

    await auth_async_loop()
