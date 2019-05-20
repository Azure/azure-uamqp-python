# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# C imports
cimport c_wsio
cimport c_tlsio
cimport c_xio


DEFAULT_WS_PORT = 443
cdef const char* DEFAULT_WS_PROTOCOL_NAME = "AMQPWSB10"
cdef const char* DEFAULT_WS_RELATIVE_PATH = "/$servicebus/websocket/"


cdef class WSIOConfig(object):

    cdef c_wsio.WSIO_CONFIG _c_value
    
    def __cinit__(self):
        self._c_value = c_wsio.WSIO_CONFIG(NULL, DEFAULT_WS_PORT, DEFAULT_WS_RELATIVE_PATH, DEFAULT_WS_PROTOCOL_NAME, NULL, NULL)
    
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

    @property
    def resource_name(self):
        return self._c_value.resource_name

    @resource_name.setter
    def resource_name(self, const char* value):
        self._c_value.resource_name = value

    @property
    def protocol(self):
        return self._c_value.protocol

    @protocol.setter
    def protocol(self, const char* value):
        self._c_value.protocol = value

    cpdef set_tlsio_config(self, IOInterfaceDescription underlying_io_interface, TLSIOConfig underlying_io_parameters):
        self._c_value.underlying_io_interface = underlying_io_interface._c_value
        self._c_value.underlying_io_parameters = &underlying_io_parameters._c_value
