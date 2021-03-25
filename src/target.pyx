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


cpdef create_target():
    target = cTarget()
    return target


cdef target_factory(c_amqp_definitions.TARGET_HANDLE c_target):
    target = cTarget()
    target.wrap(c_target)
    return target


cdef class cTarget(StructBase):

    cdef c_amqp_definitions.TARGET_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_amqp_definitions.target_create()
        self._validate()

    def __dealloc__(self):
        _logger.debug("Deallocating cTarget")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cTarget")
            c_amqp_definitions.target_destroy(self._c_value)
            self._c_value = <c_amqp_definitions.TARGET_HANDLE>NULL

    cdef wrap(self, c_amqp_definitions.TARGET_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    @property
    def value(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_amqp_definitions.amqpvalue_create_target(self._c_value)
        if <void*>_value == NULL:
            self._null_error("Failed to create target.")
        return value_factory(_value)

    @property
    def address(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.target_get_address(self._c_value, &_value) != 0:
            self._value_error("Failed to get target address")
        if <void*>_value == NULL:
            return None
        cloned = c_amqpvalue.amqpvalue_clone(_value)
        if <void*>cloned == NULL:
            return None
        return value_factory(cloned).value

    @address.setter
    def address(self, AMQPValue value):
        if c_amqp_definitions.target_set_address(self._c_value, <c_amqpvalue.AMQP_VALUE>value._c_value) != 0:
            self._value_error("Failed to set target address")

    @property
    def durable(self):
        cdef c_amqp_definitions.terminus_durability _value
        if c_amqp_definitions.target_get_durable(self._c_value, &_value) != 0:
            self._value_error("Failed to get target durable")
        if <void*>_value == NULL:
            return None
        return _value

    @durable.setter
    def durable(self, c_amqp_definitions.terminus_durability value):
        if c_amqp_definitions.target_set_durable(self._c_value, value) != 0:
            self._value_error("Failed to set target durable")

    @property
    def expiry_policy(self):
        cdef c_amqp_definitions.terminus_expiry_policy _value
        if c_amqp_definitions.target_get_expiry_policy(self._c_value, &_value) != 0:
            self._value_error("Failed to get target expiry_policy")
        if <void*>_value == NULL:
            return None
        return _value

    @expiry_policy.setter
    def expiry_policy(self, c_amqp_definitions.terminus_expiry_policy value):
        if c_amqp_definitions.target_set_expiry_policy(self._c_value, value) != 0:
            self._value_error("Failed to set target expiry_policy")

    @property
    def timeout(self):
        cdef c_amqp_definitions.seconds _value
        if c_amqp_definitions.target_get_timeout(self._c_value, &_value) != 0:
            self._value_error("Failed to get target timeout")
        if <void*>_value == NULL:
            return None
        return _value

    @timeout.setter
    def timeout(self, c_amqp_definitions.seconds value):
        if c_amqp_definitions.target_set_timeout(self._c_value, value) != 0:
            self._value_error("Failed to set target timeout")

    @property
    def dynamic(self):
        cdef bint _value
        if c_amqp_definitions.target_get_dynamic(self._c_value, &_value) != 0:
            self._value_error("Failed to get target dynamic")
        if <void*>_value == NULL:
            return None
        return _value

    @dynamic.setter
    def dynamic(self, bint value):
        if c_amqp_definitions.target_set_dynamic(self._c_value, value) != 0:
            self._value_error("Failed to set target dynamic")

    @property
    def dynamic_node_properties(self):
        cdef c_amqp_definitions.node_properties _value
        if c_amqp_definitions.target_get_dynamic_node_properties(self._c_value, &_value) != 0:
            self._value_error("Failed to get target dynamic_node_properties")
        if <void*>_value == NULL:
            return None
        return annotations_factory(_value)

    @dynamic_node_properties.setter
    def dynamic_node_properties(self, cFields value):
        if c_amqp_definitions.target_set_dynamic_node_properties(self._c_value, <c_amqp_definitions.node_properties>value._c_value) != 0:
            self._value_error("Failed to set target dynamic_node_properties")
