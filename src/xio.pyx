#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_xio
cimport c_wsio
cimport c_sasl_mechanism


_logger = logging.getLogger(__name__)


cpdef xio_from_wsioconfig(WSIOConfig io_config):
    cdef const c_xio.IO_INTERFACE_DESCRIPTION* ws_io_interface
    ws_io_interface = c_wsio.wsio_get_interface_description()
    xio = XIO()
    xio.create(ws_io_interface, io_config, &io_config._c_value)
    return xio


cpdef xio_from_tlsioconfig(IOInterfaceDescription io_desc, TLSIOConfig io_config):
    xio = XIO()
    xio.create(io_desc._c_value, io_config, &io_config._c_value)
    return xio


cpdef xio_from_saslioconfig(SASLClientIOConfig io_config):
    cdef const  c_xio.IO_INTERFACE_DESCRIPTION* interface
    interface = c_sasl_mechanism.saslclientio_get_interface_description()
    if <void*>interface == NULL:
        raise ValueError("Failed to create SASL Client IO Interface description")
    xio = XIO()
    xio.create(interface, io_config, &io_config._c_value)
    return xio


cdef class XIO(StructBase):

    cdef c_xio.XIO_HANDLE _c_value
    cdef object _io_config

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating XIO")
        self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying XIO")
            c_xio.xio_destroy(self._c_value)
            self._c_value = <c_xio.XIO_HANDLE>NULL
            self._io_config = None

    cdef wrap(self, XIO value):
        self.destroy()
        self._io_config = value._io_config
        self._c_value = value._c_value
        self._create()

    cdef create(self, c_xio.IO_INTERFACE_DESCRIPTION* io_desc, object io_config, void *io_params):
        self.destroy()
        self._io_config = io_config
        self._c_value = c_xio.xio_create(io_desc, io_params)
        self._create()

    cpdef set_option(self, const char* option_name, value):
        cdef const void* option_value
        option_value = <const void*>value
        if c_xio.xio_setoption(self._c_value, option_name, option_value) != 0:
            raise self._value_error("Failed to set option {}".format(option_name))

    cpdef set_certificates(self, bytes value):
        cdef char *certificate = value
        if c_xio.xio_setoption(self._c_value, b'TrustedCerts', <void*>certificate) != 0:
            raise self._value_error("Failed to set certificates")


cdef class IOInterfaceDescription(object):

    cdef c_xio.IO_INTERFACE_DESCRIPTION* _c_value

    def __cinit__(self):
        pass

    cdef wrap(self, c_xio.IO_INTERFACE_DESCRIPTION* value):
        self._c_value = value
