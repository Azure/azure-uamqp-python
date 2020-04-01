#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

cdef extern from "azure_c_shared_utility/xlogging.h":

    cdef enum LOG_CATEGORY_TAG:
        AZ_LOG_ERROR,
        AZ_LOG_INFO,
        AZ_LOG_TRACE

    ctypedef void(*LOGGER_LOG)(LOG_CATEGORY_TAG log_category, const char* file, const char* func, int line, unsigned int options, const char* format, ...)

    void xlogging_set_log_function(LOGGER_LOG log_function)


cdef extern from "stdarg.h":

    ctypedef struct va_list:
        pass

    ctypedef struct fake_type:
        pass

    void va_copy(va_list dest, va_list src)
    void va_start(va_list, void* arg)
    void* va_arg(va_list, fake_type)
    void va_end(va_list)
    fake_type char_type "const char*"


cdef extern from "va_copy_patch.h":
    void va_copy(va_list dest, va_list src)


cdef extern from "stdio.h":

    int vsnprintf(char* s, size_t n, const char* format, va_list arg)
    int vprintf(const char *format, va_list arg)
