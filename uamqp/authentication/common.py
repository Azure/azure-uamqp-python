#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# pylint: disable=super-init-not-called,no-self-use

import logging
import certifi

from uamqp import constants
from uamqp import c_uamqp


_logger = logging.getLogger(__name__)


class AMQPAuth:
    """AMQP authentication mixin.

    :param hostname: The AMQP endpoint hostname.
    :type hostname: str or bytes
    :param port: The TLS port - default for AMQP is 5671.
    :type port: int
    :param verify: The path to a user-defined certificate.
    :type verify: str
    :param encoding: The encoding to use if hostname is provided as a str.
     Default is 'UTF-8'.
    :type encoding: str
    """

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT, verify=None, encoding='UTF-8'):
        self._encoding = encoding
        self.hostname = hostname.encode(self._encoding) if isinstance(hostname, str) else hostname
        self.cert_file = verify
        self.sasl = _SASL()
        self.set_tlsio(self.hostname, port)

    def set_tlsio(self, hostname, port):
        """Setup the default underlying TLS IO layer. On Windows this is
        Schannel, on Linux and MacOS this is OpenSSL.

        :param hostname: The endpoint hostname.
        :type hostname: bytes
        :param port: The TLS port.
        :type port: int
        """
        _default_tlsio = c_uamqp.get_default_tlsio()
        _tlsio_config = c_uamqp.TLSIOConfig()
        _tlsio_config.hostname = hostname
        _tlsio_config.port = int(port)
        self._underlying_xio = c_uamqp.xio_from_tlsioconfig(_default_tlsio, _tlsio_config)

        cert = self.cert_file or certifi.where()
        with open(cert, 'rb') as cert_handle:
            cert_data = cert_handle.read()
            try:
                self._underlying_xio.set_certificates(cert_data)
            except ValueError:
                _logger.warning('Unable to set external certificates.')
        self.sasl_client = _SASLClient(self._underlying_xio, self.sasl)

    def close(self):
        """Close the authentication layer and cleanup
        all the authentication wrapper objects.
        """
        self.sasl.mechanism.destroy()
        self.sasl_client.get_client().destroy()
        self._underlying_xio.destroy()


class SASLPlain(AMQPAuth):
    """SASL Plain AMQP authentication.
    This is SASL authentication using a basic username and password.

    :param hostname: The AMQP endpoint hostname.
    :type hostname: str or bytes
    :param username: The authentication username.
    :type username: bytes or str
    :param password: The authentication password.
    :type password: bytes or str
    :param port: The TLS port - default for AMQP is 5671.
    :type port: int
    :param verify: The path to a user-defined certificate.
    :type verify: str
    :param encoding: The encoding to use if hostname and credentials
     are provided as a str. Default is 'UTF-8'.
    :type encoding: str
    """

    def __init__(self, hostname, username, password, port=constants.DEFAULT_AMQPS_PORT, verify=None, encoding='UTF-8'):
        self._encoding = encoding
        self.hostname = hostname.encode(self._encoding) if isinstance(hostname, str) else hostname
        self.username = username.encode(self._encoding) if isinstance(username, str) else username
        self.password = password.encode(self._encoding) if isinstance(password, str) else password
        self.cert_file = verify
        self.sasl = _SASLPlain(self.username, self.password, encoding=self._encoding)
        self.set_tlsio(self.hostname, port)


class SASLAnonymous(AMQPAuth):
    """SASL Annoymous AMQP authentication mixin.
    SASL connection with no credentials. If intending to use annoymous
    auth to set up a CBS session once connected, use SASTokenAuth
    or the CBSAuthMixin instead.

    :param hostname: The AMQP endpoint hostname.
    :type hostname: str or bytes
    :param port: The TLS port - default for AMQP is 5671.
    :type port: int
    :param verify: The path to a user-defined certificate.
    :type verify: str
    :param encoding: The encoding to use if hostname is provided as a str.
     Default is 'UTF-8'.
    :type encoding: str
    """

    def __init__(self, hostname, port=constants.DEFAULT_AMQPS_PORT, verify=None, encoding='UTF-8'):
        self._encoding = encoding
        self.hostname = hostname.encode(self._encoding) if isinstance(hostname, str) else hostname
        self.cert_file = verify
        self.sasl = _SASLAnonymous()
        self.set_tlsio(self.hostname, port)


class _SASLClient:

    def __init__(self, tls_io, sasl):
        self._tls_io = tls_io
        self._sasl_mechanism = sasl.mechanism
        self._io_config = c_uamqp.SASLClientIOConfig()
        self._io_config.underlying_io = self._tls_io
        self._io_config.sasl_mechanism = self._sasl_mechanism
        self._xio = c_uamqp.xio_from_saslioconfig(self._io_config)

    def get_client(self):
        return self._xio


class _SASL:

    def __init__(self):
        self._interface = self._get_interface()
        self.mechanism = self._get_mechanism()

    def _get_interface(self):
        return None

    def _get_mechanism(self):
        return c_uamqp.get_sasl_mechanism()


class _SASLAnonymous(_SASL):

    def _get_interface(self):
        return c_uamqp.saslanonymous_get_interface()

    def _get_mechanism(self):
        return c_uamqp.get_sasl_mechanism(self._interface)


class _SASLPlain(_SASL):

    def __init__(self, authcid, passwd, authzid=None, encoding='UTF-8'):
        self._sasl_config = c_uamqp.SASLPlainConfig()
        self._sasl_config.authcid = authcid
        self._sasl_config.passwd = passwd
        if authzid:
            self._sasl_config.authzid = authzid.encode(encoding) if isinstance(authzid, str) else authzid
        super(_SASLPlain, self).__init__()

    def _get_interface(self):
        return c_uamqp.saslplain_get_interface()

    def _get_mechanism(self):
        return c_uamqp.get_plain_sasl_mechanism(self._interface, self._sasl_config)
