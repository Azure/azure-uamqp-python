#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
from libc cimport stdint

cimport c_amqpvalue
cimport c_amqp_definitions


_logger = logging.getLogger(__name__)


cpdef create_header():
    new_header = cHeader()
    return new_header


cdef class cHeader(StructBase):

    cdef c_amqp_definitions.HEADER_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_amqp_definitions.header_create()
        self._validate()

    def __dealloc__(self):
        _logger.debug("Deallocating cHeader")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                _logger.debug("Destroying cHeader")
                c_amqp_definitions.header_destroy(self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
            self._c_value = <c_amqp_definitions.HEADER_HANDLE>NULL

    cdef wrap(self, c_amqp_definitions.HEADER_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    cpdef clone(self):
        cdef c_amqp_definitions.HEADER_HANDLE value
        value = c_amqp_definitions.header_clone(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        new_obj = cHeader()
        new_obj.wrap(value)
        return new_obj

    @property
    def delivery_count(self):
        cdef stdint.uint32_t _value
        if c_amqp_definitions.header_get_delivery_count(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @delivery_count.setter
    def delivery_count(self, stdint.uint32_t value):
        if c_amqp_definitions.header_set_delivery_count(
            self._c_value, value) != 0:
                self._value_error("Couldn't set 'delivery_count'.")

    @property
    def time_to_live(self):
        cdef c_amqp_definitions.milliseconds _value
        if c_amqp_definitions.header_get_ttl(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @time_to_live.setter
    def time_to_live(self, c_amqp_definitions.milliseconds value):
        if c_amqp_definitions.header_set_ttl(
            self._c_value, value) != 0:
                self._value_error("Couldn't set 'time_to_live'.")

    @property
    def durable(self):
        cdef bint _value
        if c_amqp_definitions.header_get_durable(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @durable.setter
    def durable(self, bint value):
        if c_amqp_definitions.header_set_durable(
            self._c_value, value) != 0:
                self._value_error("Couldn't set 'durable'.")

    @property
    def first_acquirer(self):
        cdef bint _value
        if c_amqp_definitions.header_get_first_acquirer(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @first_acquirer.setter
    def first_acquirer(self, bint value):
        if c_amqp_definitions.header_set_first_acquirer(
            self._c_value, value) != 0:
                self._value_error("Couldn't set 'first_acquirer'.")

    @property
    def priority(self):
        cdef stdint.uint8_t _value
        if c_amqp_definitions.header_get_priority(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @priority.setter
    def priority(self, stdint.uint8_t value):
        if c_amqp_definitions.header_set_priority(
            self._c_value, value) != 0:
                self._value_error("Couldn't set 'priority'.")