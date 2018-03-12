#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_xio


cdef extern from "azure_c_shared_utility/tlsio_openssl.h":

    int tlsio_openssl_init()
    void tlsio_openssl_deinit()

    c_xio.CONCRETE_IO_HANDLE tlsio_openssl_create(void* io_create_parameters)
    void tlsio_openssl_destroy(c_xio.CONCRETE_IO_HANDLE tls_io)
    int tlsio_openssl_open(c_xio.CONCRETE_IO_HANDLE tls_io, c_xio.ON_IO_OPEN_COMPLETE on_io_open_complete, void* on_io_open_complete_context, c_xio.ON_BYTES_RECEIVED on_bytes_received, void* on_bytes_received_context, c_xio.ON_IO_ERROR on_io_error, void* on_io_error_context)
    int tlsio_openssl_close(c_xio.CONCRETE_IO_HANDLE tls_io, c_xio.ON_IO_CLOSE_COMPLETE on_io_close_complete, void* callback_context)
    int tlsio_openssl_send(c_xio.CONCRETE_IO_HANDLE tls_io, const void* buffer, size_t size, c_xio.ON_SEND_COMPLETE on_send_complete, void* callback_context)
    void tlsio_openssl_dowork(c_xio.CONCRETE_IO_HANDLE tls_io)
    int tlsio_openssl_setoption(c_xio.CONCRETE_IO_HANDLE tls_io, const char* optionName, const void*,value)

    const c_xio.IO_INTERFACE_DESCRIPTION* tlsio_openssl_get_interface_description()
