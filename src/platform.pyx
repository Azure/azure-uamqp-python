#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_strings
cimport c_platform
cimport c_xio
cimport c_tlsio


_logger = logging.getLogger(__name__)


class PlatformInfoOption(Enum):
    DefaultOption = c_platform.PLATFORM_INFO_OPTION_TAG.PLATFORM_INFO_OPTION_DEFAULT
    RetrieveSQMOption = c_platform.PLATFORM_INFO_OPTION_TAG.PLATFORM_INFO_OPTION_RETRIEVE_SQM


cpdef platform_init():
    if c_platform.platform_init() != 0:
        raise ValueError("Failed to initialize platform.")


cpdef platform_deinit():
    _logger.debug("Deinitializing platform")
    c_platform.platform_deinit()


cpdef get_info():
    cdef c_strings.STRING_HANDLE str_info
    str_info = c_platform.platform_get_platform_info(PlatformInfoOption.DefaultOption)
    info = AMQPString()
    info.wrap(str_info)
    return info


cpdef get_default_tlsio():
    cdef const c_xio.IO_INTERFACE_DESCRIPTION* io_desc
    io_desc = c_platform.platform_get_default_tlsio()
    if <void*>io_desc == NULL:
        raise ValueError("Failed to create tlsio description.")

    interface = IOInterfaceDescription()
    interface.wrap(io_desc)
    return interface
