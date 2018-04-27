#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import sys
import logging
import time
import datetime
import threading
import certifi
try:
    from urllib import quote_plus, unquote_plus #Py2
    from urllib import urlparse
except Exception:
    from urllib.parse import quote_plus, unquote_plus
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
    return c_uamqp.get_default_tlsio()


class TokenRetryPolicy:

    def __init__(self, retries=3, backoff=0):
        self.retries = retries
        self.backoff = backoff


class AMQPAuth:

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT, verify=None):
        self.hostname = hostname.encode('utf-8')
        self.cert_file = verify
        self.sasl = sasl.SASL()
        self.set_tlsio(hostname, port)

    def set_tlsio(self, hostname, port):
        self._default_tlsio = _get_default_tlsio()
        self._tlsio_config = c_uamqp.TLSIOConfig()
        self._tlsio_config.hostname = hostname.encode('utf-8') if isinstance(hostname, str) else hostname
        self._tlsio_config.port = int(port)
        self._underlying_xio = c_uamqp.xio_from_tlsioconfig(self._default_tlsio, self._tlsio_config)

        cert = self.cert_file or certifi.where()
        with open(cert, 'rb') as cert_handle:
            cert_data = cert_handle.read()
            self._underlying_xio.set_certificates(cert_data)
        self.sasl_client = sasl.SASLClient(self._underlying_xio, self.sasl)

    def close(self):
        self.sasl.mechanism.destroy()
        self.sasl_client.get_client().destroy()
        self._underlying_xio.destroy()


class SASLPlain(AMQPAuth):

    def __init__(self, hostname, username, password, port=constants.DEFAULT_AMQPS_PORT, verify=None):
        self.hostname = hostname.encode('utf-8')
        self.username = username.encode('utf-8') if isinstance(username, str) else username
        self.password = password.encode('utf-8') if isinstance(password, str) else password
        self.cert_file = verify
        self.sasl = sasl.SASLPlain(self.username, self.password)
        self.set_tlsio(hostname, port)


class SASLAnonymous(AMQPAuth):

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT, verify=None):
        self.hostname = hostname.encode('utf-8')
        self.cert_file = verify
        self.sasl = sasl.SASLAnonymous()
        self.set_tlsio(hostname, port)


class CBSAuthMixin:

    def update_token(self):
        raise errors.TokenExpired(
            "Unable to refresh token - no refresh logic implemented.")

    def create_authenticator(self, connection, debug=False):
        self._lock = threading.Lock()
        self._session = Session(
            connection,
            incoming_window=constants.MAX_FRAME_SIZE_BYTES,
            outgoing_window=constants.MAX_FRAME_SIZE_BYTES)
        try:
            self._cbs_auth = c_uamqp.CBSTokenAuth(
                self.audience,
                self.token_type,
                self.token,
                int(self.expires_at),
                self._session._session,
                self.timeout)
            self._cbs_auth.set_trace(debug)
        except ValueError:
            raise errors.AMQPConnectionError(
                "Unable to open authentication session. "
                "Please confirm target URI exists.")
        return self._cbs_auth

    def close_authenticator(self):
        self._cbs_auth.destroy()
        self._session.destroy()

    def handle_token(self):
        timeout = False
        in_progress = False
        self._lock.acquire()
        try:
            auth_status = self._cbs_auth.get_status()
            auth_status = constants.CBSAuthStatus(auth_status)
            if auth_status == constants.CBSAuthStatus.Error:
                if self.retries >= self._retry_policy.retries:
                    _logger.warning("Authentication Put-Token failed. Retries exhausted.")
                    raise errors.TokenAuthFailure(*self._cbs_auth.get_failure_info())
                else:
                    _logger.info("Authentication Put-Token failed. Retrying.")
                    self.retries += 1
                    time.sleep(self._retry_policy.backoff)
                    self._cbs_auth.authenticate()
                    in_progress = True
            elif auth_status == constants.CBSAuthStatus.Failure:
                errors.AuthenticationException("Failed to open CBS authentication link.")
            elif auth_status == constants.CBSAuthStatus.Expired:
                raise errors.TokenExpired("CBS Authentication Expired.")
            elif auth_status == constants.CBSAuthStatus.Timeout:
                timeout = True
            elif auth_status == constants.CBSAuthStatus.InProgress:
                in_progress = True
            elif auth_status == constants.CBSAuthStatus.RefreshRequired:
                _logger.info("Token will expire soon - attempting to refresh.")
                self.update_token()
                self._cbs_auth.refresh(self.token, int(self.expires_at))
            elif auth_status == constants.CBSAuthStatus.Idle:
                self._cbs_auth.authenticate()
                in_progress = True
            elif auth_status != constants.CBSAuthStatus.Ok:
                raise errors.AuthenticationException("Invalid auth state.")
        except ValueError as e:
            raise errors.AuthenticationException(
                "Token authentication failed: {}".format(e))
        except:
            raise
        finally:
            self._lock.release()
        return timeout, in_progress


class SASTokenAuth(AMQPAuth, CBSAuthMixin):

    def __init__(self, audience, uri, token,
                 expires_in=None,
                 expires_at=None,
                 username=None,
                 password=None,
                 port=constants.DEFAULT_AMQPS_PORT,
                 timeout=10,
                 retry_policy=TokenRetryPolicy(),
                 verify=None,
                 token_type=b"servicebus.windows.net:sastoken"):
        self._retry_policy = retry_policy
        parsed = urlparse(uri)
        self.uri = uri
        self.cert_file = verify
        self.hostname = parsed.hostname
        self.username = unquote_plus(parsed.username) if parsed.username else None
        self.username = username or self.username
        self.password = unquote_plus(parsed.password) if parsed.password else None
        self.password = password or self.password
        self.audience = audience if isinstance(audience, bytes) else audience.encode('utf-8')
        self.token_type = token_type if isinstance(token_type, bytes) else token_type.encode('utf-8')
        self.token = token if isinstance(token, bytes) else token.encode('utf-8')
        if not expires_at and not expires_in:
            raise ValueError("Must specify either 'expires_at' or 'expires_in'.")
        elif not expires_at:
            self.expires_in = expires_in
            self.expires_at = time.time() + expires_in.seconds
        else:
            self.expires_at = expires_at
            expires_in = expires_at - time.time()
            if expires_in < 1:
                raise ValueError("Token has already expired.")
            self.expires_in = datetime.timedelta(seconds=expires_in)
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

    def update_token(self):
        if not self.username or not self.password:
            raise errors.TokenExpired("Unable to refresh token - no username or password.")
        encoded_uri = quote_plus(self.uri)
        encoded_key = quote_plus(self.username)
        self.expires_at = time.time() + self.expires_in.seconds
        self.token = utils.create_sas_token(encoded_key, self.password, encoded_uri, self.expires_in)

    @classmethod
    def from_shared_access_key(
            cls,
            uri,
            key_name,
            shared_access_key,
            expiry=None,
            timeout=10):
        expires_in = datetime.timedelta(seconds=expiry or constants.AUTH_EXPIRATION_SECS)
        encoded_uri = quote_plus(uri)
        encoded_key = quote_plus(key_name)
        expires_at = time.time() + expires_in.seconds
        token = utils.create_sas_token(encoded_key, shared_access_key, encoded_uri, expires_in)
        return cls(
            uri, uri, token,
            expires_in=expires_in,
            expires_at=expires_at,
            timeout=timeout,
            username=key_name,
            password=shared_access_key)
