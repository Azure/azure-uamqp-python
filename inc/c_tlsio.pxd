#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_xio


cdef extern from "./azure-c-shared-utility/inc/azure_c_shared_utility/tlsio.h":

    ctypedef struct TLSIO_CONFIG_TAG:
        const char* hostname
        int port
        const c_xio.IO_INTERFACE_DESCRIPTION* underlying_io_interface
        void* underlying_io_parameters

    ctypedef TLSIO_CONFIG_TAG TLSIO_CONFIG
