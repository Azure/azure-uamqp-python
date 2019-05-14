#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_xio


cdef extern from "azure_c_shared_utility/wsio.h":

    ctypedef struct WSIO_CONFIG_TAG:
        const char* hostname
        int port
        const char* resource_name
        const char* protocol
        const c_xio.IO_INTERFACE_DESCRIPTION* underlying_io_interface
        void* underlying_io_parameters

    ctypedef WSIO_CONFIG_TAG WSIO_CONFIG

    const c_xio.IO_INTERFACE_DESCRIPTION* wsio_get_interface_description()
