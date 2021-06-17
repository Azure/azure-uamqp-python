#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#-------------------------------------------------------------------------

import time
import urllib
import hmac
import hashlib
import base64
from collections import namedtuple
from functools import partial

from .sasl import SASLAnonymousCredential, SASLPlainCredential

from .constants import (
    AUTH_DEFAULT_EXPIRATION_SECONDS,
    AUTH_TIMEOUT,
    TOKEN_TYPE_JWT,
    TOKEN_TYPE_SASTOKEN
)

try:
    from urlparse import urlparse
    from urllib import quote_plus  # type: ignore
except ImportError:
    from urllib.parse import urlparse, quote_plus

AccessToken = namedtuple("AccessToken", ["token", "expires_on"])


def _generate_sas_token(auth_uri, sas_name, sas_key, expiry_in=AUTH_DEFAULT_EXPIRATION_SECONDS):
    auth_uri = urllib.parse.quote_plus(auth_uri)
    sas = sas_key.encode("utf-8")
    expires_on = int(time.time() + expiry_in)
    string_to_sign = (auth_uri + '\n' + str(expires_on)).encode('utf-8')
    signed_hmac_sha256 = hmac.HMAC(sas, string_to_sign, hashlib.sha256)
    signature = urllib.parse.quote(base64.b64encode(signed_hmac_sha256.digest()))
    return AccessToken(
        "SharedAccessSignature sr={}&sig={}&se={}&skn={}".format(auth_uri, signature, str(expires_on), sas_name),
        expires_on
    )


class SASLPlainAuth(object):
    def __init__(self, authcid, passwd, authzid=None):
        self.sasl = SASLPlainCredential(authcid, passwd, authzid)


class _CBSAuth(object):
    def __init__(
        self,
        uri,
        auth_audience,
        token_type,
        get_token,
        expires_in=AUTH_DEFAULT_EXPIRATION_SECONDS,
        expires_on=None,
        auth_timeout=AUTH_TIMEOUT,
    ):
        self.sasl = SASLAnonymousCredential()
        self.uri = uri
        self.auth_audience = auth_audience
        self.token_type = token_type
        self.auth_timeout = auth_timeout
        self.get_token = get_token
        self.expires_in = expires_in
        self.expires_on = expires_on

    @staticmethod
    def _set_expiry(expires_in, expires_on):
        if not expires_on and not expires_in:
            raise ValueError("Must specify either 'expires_on' or 'expires_in'.")
        if not expires_on:
            expires_on = time.time() + expires_in
        else:
            expires_in = expires_on - time.time()
            if expires_in < 1:
                raise ValueError("Token has already expired.")
        return expires_in, expires_on


class JWTTokenAuth(_CBSAuth):
    def __init__(
        self,
        uri,
        audience,
        get_token,
        auth_timeout=AUTH_TIMEOUT,
        token_type=TOKEN_TYPE_JWT,
        **kwargs
    ):
        super(JWTTokenAuth, self).__init__(uri, audience, token_type, auth_timeout)
        self.get_token = get_token


class SASTokenAuth(_CBSAuth):
    def __init__(
        self,
        uri,
        audience,
        username,
        password,
        expires_in=AUTH_DEFAULT_EXPIRATION_SECONDS,
        expires_on=None,
        auth_timeout=AUTH_TIMEOUT,
        token_type=TOKEN_TYPE_SASTOKEN,
        **kwargs
    ):
        self.username = username
        self.password = password
        expires_in, expires_on = self._set_expiry(expires_in, expires_on)
        self.get_token = partial(_generate_sas_token, uri, username, password, expires_in)
        super(SASTokenAuth, self).__init__(
            uri,
            audience,
            token_type,
            self.get_token,
            expires_in,
            expires_on,
            auth_timeout
        )
