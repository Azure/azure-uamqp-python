#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# C imports
cimport c_tlsio
cimport c_xio


DEFAULT_PORT = 5671


cdef class TLSIOConfig:

    cdef c_tlsio.TLSIO_CONFIG _c_value

    def __cinit__(self):
        self._c_value = c_tlsio.TLSIO_CONFIG(NULL, DEFAULT_PORT, NULL, NULL)

    @property
    def hostname(self):
        return self._c_value.hostname

    @hostname.setter
    def hostname(self, const char* value):
        self._c_value.hostname = value

    @property
    def port(self):
        return self._c_value.port

    @port.setter
    def port(self, int port):
        self._c_value.port = port
