#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------
"""
Examples to show how to authenticate Client by jwt token.
"""

from collections import namedtuple

from uamqp import authentication, SendClient, Message

AccessToken = namedtuple("AccessToken", ["token", "expires_on"])


# Define get_token callback which shall be passed to the JWTTokenAuth for token generation
def get_token():
    token = "<token>"  # the token used for authentication.
    expires_on = 253402261199  # The timestamp at which the JWT token will expire formatted as seconds since epoch.
    return AccessToken(token, expires_on)


def authenticate_client_by_jwt():
    # Create the JWTTokenAuth object
    auth_uri = "<amqp endpoint uri for authentication>"  # The AMQP endpoint URI for authentication.
    token_audience = "<token audience>"  # The token audience field.
    auth = authentication.JWTTokenAuth(
        audience=token_audience,
        uri=auth_uri,
        get_token=get_token
    )

    # Instantiate the SendClient with the JWTTokenAuth object
    target = "<target amqp service endpoint>"  # The target AMQP service endpoint.
    send_client = SendClient(target=target, auth=auth)

    # Send a message
    message = Message(b'data')
    send_client.send_message(message)
    send_client.close()


if __name__ == "__main__":
    authenticate_client_by_jwt()