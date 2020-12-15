#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_strings
cimport c_xio


cdef extern from "azure_c_shared_utility/platform.h":

    cdef enum PLATFORM_INFO_OPTION_TAG:
        PLATFORM_INFO_OPTION_DEFAULT,
        PLATFORM_INFO_OPTION_RETRIEVE_SQM,

    int platform_init()
    void platform_deinit()
    const c_xio.IO_INTERFACE_DESCRIPTION* platform_get_default_tlsio()
    c_strings.STRING_HANDLE platform_get_platform_info(PLATFORM_INFO_OPTION_TAG options)
