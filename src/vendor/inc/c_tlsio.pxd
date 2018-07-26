#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_xio


cdef extern from "azure_c_shared_utility/tlsio.h":

    ctypedef struct TLSIO_CONFIG_TAG:
        const char* hostname
        int port
        const c_xio.IO_INTERFACE_DESCRIPTION* underlying_io_interface
        void* underlying_io_parameters

    ctypedef TLSIO_CONFIG_TAG TLSIO_CONFIG


cdef extern from "azure_c_shared_utility/http_proxy_io.h":

    ctypedef struct HTTP_PROXY_IO_CONFIG_TAG:
        const char* hostname
        int port
        const char* proxy_hostname
        int proxy_port
        const char* username
        const char* password

    ctypedef HTTP_PROXY_IO_CONFIG_TAG HTTP_PROXY_IO_CONFIG

    const c_xio.IO_INTERFACE_DESCRIPTION* http_proxy_io_get_interface_description()