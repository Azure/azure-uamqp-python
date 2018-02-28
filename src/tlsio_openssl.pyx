#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_xio
cimport c_tlsio_openssl


_logger = logging.getLogger(__name__)


cpdef tlsio_openssl_init():
    if c_tlsio_openssl.tlsio_openssl_init() != 0:
        raise ValueError("TLSIO initialization failed")


cpdef tlsio_openssl_deinit():
    _logger.debug("Deinitializing OpenSSL platform")
    c_tlsio_openssl.tlsio_openssl_deinit()


cpdef get_openssl_tlsio():
    cdef const c_xio.IO_INTERFACE_DESCRIPTION* io_desc
    io_desc = c_tlsio_openssl.tlsio_openssl_get_interface_description()
    if <void*>io_desc == NULL:
        raise ValueError("Failed to create OpenSSL defaults.")

    interface = IOInterfaceDescription()
    interface.wrap(io_desc)
    return interface
