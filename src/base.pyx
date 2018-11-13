#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_tlsio
cimport c_utils


_logger = logging.getLogger(__name__)


cdef class StructBase(object):
    """Base class for wrapped C structs."""

    def _memory_error(self):
        message = "Failed to allocate memory to create {}"
        raise MemoryError(message.format(self.__class__.__name__))

    def _value_error(self, error_message=None, error_code=None):
        message = "Operation failed."
        if error_message:
            message += "\nError: {}".format(error_message)
        if error_code:
            message += "\nErrorCode: {}".format(error_code)
        raise ValueError(message)

    def _null_error(self, error_message=None):
        message = "NULL error occurred in {}.".format(self.__class__.__name__)
        if error_message:
            message += "\nError: {}".format(error_message)
        raise ValueError(message)


cdef class TickCounter(object):

    cdef c_utils.TICK_COUNTER_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_utils.tickcounter_create()
        if <void*>self._c_value == NULL:
            raise MemoryError("Failed to create tick counter.")

    def __dealloc__(self):
        self.destroy()

    cpdef destroy(self):
        if <void*>self._c_value != NULL:
            c_utils.tickcounter_destroy(self._c_value)
            self._c_value = <c_utils.TICK_COUNTER_HANDLE>NULL

    cpdef get_current_ms(self):
        cdef c_utils.tickcounter_ms_t current_ms
        if c_utils.tickcounter_get_current_ms(self._c_value, &current_ms) != 0:
            raise ValueError("Failed to get current ms time.")
        return current_ms
