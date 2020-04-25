#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
import six

from .management_link import ManagementLink
from .message import Message, Properties
from .constants import (
    CbsState,
    AUTH_TIMEOUT,
    TOKEN_TYPE_SASTOKEN,
    CBS_PUT_TOKEN,
    CBS_EXPIRATION,
    CBS_NAME,
    CBS_TYPE,
    CBS_OPERATION
)


class CbsAuth(object):
    def __init__(
            self,
            session,
            auth_audience,
            get_token,
            token_type=TOKEN_TYPE_SASTOKEN,
            auth_timeout=AUTH_TIMEOUT,
            encoding='UTF-8'
    ):
        self._session = session
        self._mgmt_link = self._session.create_request_response_link_pair('$cbs')  # type: ManagementLink
        self._auth_audience = auth_audience
        self._encoding = encoding
        self._auth_timeout = auth_timeout

        if not get_token or not callable(get_token):
            raise ValueError("get_token must be a callable object.")

        self._get_token = get_token
        self._token_type = token_type
        self._expires_at = None
        self._token = None

        self.state = CbsState.CLOSED

    def _encode(self, value):
        return value.encode(self._encoding) if isinstance(value, six.text_type) else value

    def _put_token(self, token, token_type, audience, expiration_at=None):
        # type: (str, str, str, int) -> None
        message = Message(
            value=token,
            properties=Properties(message_id=self._mgmt_link.next_message_id),
            application_properties={
                CBS_NAME: audience,
                CBS_OPERATION: CBS_PUT_TOKEN,
                CBS_TYPE: token_type,
                CBS_EXPIRATION: expiration_at
            }
        )
        self._mgmt_link.next_message_id += 1
        self._mgmt_link._request_link.send_transfer(
            message,
            on_send_complete=self._on_put_token_complete,
            timeout=self._auth_timeout
        )

    def _on_put_token_complete(self, message, reason, state):
        pass

    def open(self):
        self.state = CbsState.OPENING

    def close(self):
        self.state = CbsState.CLOSED

    def update_token(self):
        access_token = self._get_token()
        self._expires_at = access_token.expires_on
        self._token = access_token.token
        self._put_token(self._token, self._token_type, self._auth_audience, self._expires_at)

    def delete_token(self, token_type, audience):
        pass
