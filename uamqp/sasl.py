#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

try:
    from urllib import quote_plus #Py2
except Exception:
    from urllib.parse import quote_plus

from uamqp import c_uamqp


class SASLClient:

    def __init__(self, tls_io, sasl):
        self._tls_io = tls_io
        self._sasl_mechanism = sasl.mechanism
        self._io_config = c_uamqp.SASLClientIOConfig()
        self._io_config.underlying_io = self._tls_io
        self._io_config.sasl_mechanism = self._sasl_mechanism
        self._xio = c_uamqp.xio_from_saslioconfig(self._io_config)

    def get_client(self):
        return self._xio


class SASL:

    def __init__(self):
        self._interface = self._get_interface()
        self.mechanism = self._get_mechanism()

    def _get_interface(self):
        return None

    def _get_mechanism(self):
        return c_uamqp.get_sasl_mechanism()


class SASLAnonymous(SASL):

    def _get_interface(self):
        return c_uamqp.saslanonymous_get_interface()

    def _get_mechanism(self):
        return c_uamqp.get_sasl_mechanism(self._interface)


class SASLPlain(SASL):

    def __init__(self, authcid, passwd, authzid=None):
        self._sasl_config = c_uamqp.SASLPlainConfig()
        self._sasl_config.authcid = authcid
        self._sasl_config.passwd = passwd
        if authzid:
            self._sasl_config.authzid = authzid.encode('utf-8')
        super(SASLPlain, self).__init__()

    def _get_interface(self):
        return c_uamqp.saslplain_get_interface()

    def _get_mechanism(self):
        return c_uamqp.get_plain_sasl_mechanism(self._interface, self._sasl_config)
