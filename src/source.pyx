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


cpdef create_source():
    source = cSource()
    return source


cdef source_factory(c_amqp_definitions.SOURCE_HANDLE c_source):
    source = cSource()
    source.wrap(c_source)
    return source


cdef class cSource(StructBase):

    cdef c_amqp_definitions.SOURCE_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_amqp_definitions.source_create()
        self._validate()

    def __dealloc__(self):
        _logger.debug("Deallocating cSource")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cSource")
            c_amqp_definitions.source_destroy(self._c_value)
            self._c_value = <c_amqp_definitions.SOURCE_HANDLE>NULL

    cdef wrap(self, c_amqp_definitions.SOURCE_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    @property
    def value(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_amqp_definitions.amqpvalue_create_source(self._c_value)
        if <void*>_value == NULL:
            self._null_error("Failed to create source.")
        return value_factory(_value)

    @property
    def address(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.source_get_address(self._c_value, &_value) != 0:
            self._value_error("Failed to get source address")
        if <void*>_value == NULL:
            return None
        cloned = c_amqpvalue.amqpvalue_clone(_value)
        if <void*>cloned == NULL:
            return None
        return value_factory(cloned).value

    @address.setter
    def address(self, AMQPValue value):
        if c_amqp_definitions.source_set_address(self._c_value, <c_amqpvalue.AMQP_VALUE>value._c_value) != 0:
            self._value_error("Failed to set source address")

    @property
    def durable(self):
        cdef c_amqp_definitions.terminus_durability _value
        if c_amqp_definitions.source_get_durable(self._c_value, &_value) != 0:
            self._value_error("Failed to get source durable")
        if <void*>_value == NULL:
            return None
        return _value

    @durable.setter
    def durable(self, c_amqp_definitions.terminus_durability value):
        if c_amqp_definitions.source_set_durable(self._c_value, value) != 0:
            self._value_error("Failed to set source durable")

    @property
    def expiry_policy(self):
        cdef c_amqp_definitions.terminus_expiry_policy _value
        if c_amqp_definitions.source_get_expiry_policy(self._c_value, &_value) != 0:
            self._value_error("Failed to get source expiry_policy")
        if <void*>_value == NULL:
            return None
        return _value

    @expiry_policy.setter
    def expiry_policy(self, c_amqp_definitions.terminus_expiry_policy value):
        if c_amqp_definitions.source_set_expiry_policy(self._c_value, value) != 0:
            self._value_error("Failed to set source expiry_policy")

    @property
    def timeout(self):
        cdef c_amqp_definitions.seconds _value
        if c_amqp_definitions.source_get_timeout(self._c_value, &_value) != 0:
            self._value_error("Failed to get source timeout")
        if <void*>_value == NULL:
            return None
        return _value

    @timeout.setter
    def timeout(self, c_amqp_definitions.seconds value):
        if c_amqp_definitions.source_set_timeout(self._c_value, value) != 0:
            self._value_error("Failed to set source timeout")

    @property
    def dynamic(self):
        cdef bint _value
        if c_amqp_definitions.source_get_dynamic(self._c_value, &_value) != 0:
            self._value_error("Failed to get source dynamic")
        if <void*>_value == NULL:
            return None
        return _value

    @dynamic.setter
    def dynamic(self, bint value):
        if c_amqp_definitions.source_set_dynamic(self._c_value, value) != 0:
            self._value_error("Failed to set source dynamic")

    @property
    def dynamic_node_properties(self):
        cdef c_amqp_definitions.node_properties _value
        if c_amqp_definitions.source_get_dynamic_node_properties(self._c_value, &_value) != 0:
            self._value_error("Failed to get source dynamic_node_properties")
        if <void*>_value == NULL:
            return None
        return annotations_factory(_value)

    @dynamic_node_properties.setter
    def dynamic_node_properties(self, cFields value):
        if c_amqp_definitions.source_set_dynamic_node_properties(self._c_value, <c_amqp_definitions.node_properties>value._c_value) != 0:
            self._value_error("Failed to set source dynamic_node_properties")

    @property
    def distribution_mode(self):
        cdef const char* _value
        if c_amqp_definitions.source_get_distribution_mode(self._c_value, &_value) != 0:
            self._value_error("Failed to get source distribution_mode")
        if <void*>_value == NULL:
            return None
        return _value

    @distribution_mode.setter
    def distribution_mode(self, const char* value):
        if c_amqp_definitions.source_set_distribution_mode(self._c_value, value) != 0:
            self._value_error("Failed to set source distribution_mode")

    @property
    def filter_set(self):
        cdef c_amqp_definitions.filter_set _value
        cdef c_amqp_definitions.filter_set clone
        if c_amqp_definitions.source_get_filter(self._c_value, &_value) != 0:
            self._value_error("Failed to get source filter_set")
        if <void*>_value == NULL:
            return None
        cloned = c_amqpvalue.amqpvalue_clone(_value)
        if <void*>cloned == NULL:
            return None
        return value_factory(cloned)

    @filter_set.setter
    def filter_set(self, AMQPValue value):
        if c_amqp_definitions.source_set_filter(self._c_value, <c_amqp_definitions.filter_set>value._c_value) != 0:
            self._value_error("Failed to set source filter_set")
