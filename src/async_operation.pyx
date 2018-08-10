#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_async_operation


_logger = logging.getLogger(__name__)


cdef class AsyncOperation(StructBase):

    cdef c_async_operation.ASYNC_OPERATION_HANDLE _c_value

    def __cinit__(self):
        pass

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying AsyncOperation")
            c_async_operation.async_operation_destroy(self._c_value)
            self._c_value = <c_async_operation.ASYNC_OPERATION_HANDLE>NULL

    cdef wrap(self, c_async_operation.ASYNC_OPERATION_HANDLE value):
        self.destroy()
        self._c_value = value
        self._create()

    cpdef cancel(self):
        if c_async_operation.async_operation_cancel(self._c_value) != 0:
            self._value_error()
