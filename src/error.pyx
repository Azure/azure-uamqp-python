#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging
import copy

# C imports
cimport c_amqp_definitions
cimport c_amqpvalue


_logger = logging.getLogger(__name__)


cpdef create_error(const char* condition_value):
    new_error = cError()
    new_error.create(condition_value)
    return new_error

cdef error_factory(c_amqp_definitions.ERROR_HANDLE error):
    wrapper = cError()
    wrapper.wrap(error)
    return wrapper


cdef class cError(StructBase):

    cdef c_amqp_definitions.ERROR_HANDLE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating cError")
        #self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cError")
            c_amqp_definitions.error_destroy(self._c_value)
            self._c_value = <c_amqp_definitions.ERROR_HANDLE>NULL

    cdef wrap(self, c_amqp_definitions.ERROR_HANDLE value):
        self.destroy()
        self._c_value = value
        self._create()

    cdef create(self, const char* condition_value):
        self.destroy()
        self._c_value = c_amqp_definitions.error_create(condition_value)
        self._create()

    @property
    def condition(self):
        cdef const char* condition_value
        if  c_amqp_definitions.error_get_condition(self._c_value, &condition_value) != 0:
            self._value_error()
        return condition_value

    @condition.setter
    def condition(self, const char* condition_value):
        if c_amqp_definitions.error_set_condition(self._c_value, condition_value) != 0:
            self._value_error()

    @property
    def description(self):
        cdef const char* description_value
        if  c_amqp_definitions.error_get_description(self._c_value, &description_value) != 0:
            return None
        return description_value

    @description.setter
    def description(self, const char* description_value):
        if c_amqp_definitions.error_set_description(self._c_value, description_value) != 0:
            self._value_error()

    @property
    def info(self):
        cdef c_amqp_definitions.fields info_value
        if  c_amqp_definitions.error_get_info(self._c_value, &info_value) != 0:
            return None
        try:
            info = value_factory(info_value)
            return copy.deepcopy(info.value)
        except TypeError:
            return None

    @info.setter
    def info(self, AMQPValue info_value):
        if c_amqp_definitions.error_set_info(self._c_value, <c_amqp_definitions.fields>info_value._c_value) != 0:
            self._value_error()