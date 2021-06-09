#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------
"""
Examples to show how to authenticate Client by jwt token asynchronously.
"""

import asyncio
from collections import namedtuple

from uamqp import authentication, SendClientAsync, Message

AccessToken = namedtuple("AccessToken", ["token", "expires_on"])


# Define get_token callback which shall be passed to the JWTTokenAsync for token generation
async def get_token():
    token = "<token>"  # the token used for authentication.
    expires_on = 253402261199  # The timestamp at which the JWT token will expire formatted as seconds since epoch.
    return AccessToken(token, expires_on)


async def authenticate_client_by_jwt():
    # Create the JWTTokenAsync object
    auth_uri = "<amqp endpoint uri for authentication>"  # The AMQP endpoint URI for authentication.
    token_audience = "<token audience>"  # The token audience field.
    auth = authentication.JWTTokenAsync(
        audience=token_audience,
        uri=auth_uri,
        get_token=get_token
    )

    # Instantiate the SendClient with the JWTTokenAsync object
    target = "<target amqp service endpoint>"  # The target AMQP service endpoint.
    send_client = SendClientAsync(target=target, auth=auth)

    # Send a message
    message = Message(b'data')
    await send_client.send_message_async(message)
    await send_client.close_async()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(authenticate_client_by_jwt())
