#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import sys
import logging
import time
import datetime
try:
    from urllib import quote_plus #Py2
    from urllib import urlparse
except Exception:
    from urllib.parse import quote_plus
    from urllib.parse import urlparse

from uamqp import Session
from uamqp import utils
from uamqp import sasl
from uamqp import constants
from uamqp import errors
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)
_is_win = sys.platform.startswith('win')


def _get_default_tlsio():
    if _is_win:
        return c_uamqp.get_default_tlsio()
    else:
        return c_uamqp.get_openssl_tlsio()


class TokenRetryPolicy:

    def __init__(self, retries=3, backoff=0):
        self.retries = retries
        self.backoff = backoff


class AMQPAuth:

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT):
        self.hostname = hostname.encode('utf-8')
        self.sasl = sasl.SASL()
        self.set_tlsio(hostname, port)

    def set_tlsio(self, hostname, port):
        self._default_tlsio = _get_default_tlsio()
        self._tlsio_config = c_uamqp.TLSIOConfig()
        self._tlsio_config.hostname = hostname.encode('utf-8') if isinstance(hostname, str) else hostname
        self._tlsio_config.port = int(port)
        self._underlying_xio = c_uamqp.xio_from_tlsioconfig(self._default_tlsio, self._tlsio_config)
        self.sasl_client = sasl.SASLClient(self._underlying_xio, self.sasl)

    def close(self):
        self.sasl.mechanism.destroy()
        self.sasl_client.get_client().destroy()
        self._underlying_xio.destroy()


class SASLPlain(AMQPAuth):

    def __init__(self, hostname, username, password, port=constants.DEFAULT_AMQPS_PORT):
        self.hostname = hostname.encode('utf-8')
        self.username = username.encode('utf-8') if isinstance(username, str) else username
        self.password = password.encode('utf-8') if isinstance(password, str) else password
        self.sasl = sasl.SASLPlain(self.username, self.password)
        self.set_tlsio(hostname, port)


class SASLAnonymous(AMQPAuth):

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT):
        self.hostname = hostname.encode('utf-8')
        self.sasl = sasl.SASLAnonymous()
        self.set_tlsio(hostname, port)


class CBSAuthMixin:

    def configure(self):
        raise NotImplementedError(
            "Token auth must implement configuration."
        )

    def create_authenticator(self, connection, debug=False):
        self._session = Session(
            connection,
            incoming_window=constants.MAX_FRAME_SIZE_BYTES,
            outgoing_window=constants.MAX_FRAME_SIZE_BYTES)
        self._cbs_auth = c_uamqp.CBSTokenAuth(
            self.audience,
            self.token_type,
            self.token,
            self.expiry,
            self._session._session,
            self.timeout)
        self._cbs_auth.set_trace(debug)
        return self._cbs_auth

    def close_authenticator(self):
        self._cbs_auth.destroy()
        self._session.destroy()

    def refresh_token_async(self, token):
        self._refresh_token = token

    def handle_token(self):
        timeout = False
        in_progress = False
        auth_status = self._cbs_auth.get_status()
        auth_status = constants.CBSAuthStatus(auth_status)
        if auth_status == constants.CBSAuthStatus.Failure:
            if self.retries >= self._retry_policy.retries:
                raise errors.TokenAuthFailure(*self._cbs_auth.get_failure_info())
            else:
                self.retries += 1
                time.sleep(self._retry_policy.backoff)
                self._cbs_auth.authenticate()
                in_progress = True
        elif auth_status == constants.CBSAuthStatus.Expired:
            raise errors.TokenExpired("CBS Authentication Expired.")
        elif auth_status == constants.CBSAuthStatus.Timeout:
            timeout = True
        elif auth_status == constants.CBSAuthStatus.InProgress:
            in_progress = True
        elif auth_status == constants.CBSAuthStatus.RefreshRequired:
            self._cbs_auth.refresh(None)
        elif auth_status == constants.CBSAuthStatus.Idle:
            self._cbs_auth.authenticate()
            in_progress = True
        elif auth_status == constants.CBSAuthStatus.Ok:
            if self._refresh_token:
                try:
                    self._cbs_auth.refresh(self._refresh_token)
                finally:
                    self._refresh_token = None
        else:
            raise ValueError("Invalid auth state.")
        return timeout, in_progress


class SASTokenAuth(AMQPAuth, CBSAuthMixin):

    def __init__(self, audience, uri, token, expiry,
                 port=constants.DEFAULT_AMQPS_PORT, timeout=10,
                 retry_policy=TokenRetryPolicy(),
                 token_type=b"servicebus.windows.net:sastoken"):
        self._refresh_token = None
        self._retry_policy = retry_policy
        parsed = urlparse(uri)
        self.hostname = parsed.hostname
        self.audience = audience if isinstance(audience, bytes) else audience.encode('utf-8')
        self.token_type = token_type if isinstance(token_type, bytes) else token_type.encode('utf-8')
        self.token = token if isinstance(token, bytes) else token.encode('utf-8')
        self.expiry = expiry
        self.timeout = timeout
        self.retries = 0

        self.sasl = sasl.SASL()
        self.set_tlsio(self.hostname, port)

    def close(self):
        super(SASTokenAuth, self).close()

    @classmethod
    def from_connection_string(cls, connection_str):
        raise NotImplementedError()

    @classmethod
    def from_sas_token(cls, sas_token):
        raise NotImplementedError()

    @classmethod
    def from_shared_access_key(
            cls,
            uri,
            key_name,
            shared_access_key,
            expiry=None,
            timeout=10):
        expiry = expiry or constants.AUTH_EXPIRATION_SECS
        expiry = int(time.time()) + expiry
        encoded_uri = quote_plus(uri)
        encoded_key = quote_plus(key_name)
        token = utils.create_sas_token(encoded_key, shared_access_key, encoded_uri)
        return cls(uri, uri, token, expiry, timeout=timeout)
