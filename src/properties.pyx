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
cimport c_utils


_logger = logging.getLogger(__name__)


cpdef create_properties():
    new_props = cProperties()
    return new_props


cpdef load_properties(AMQPValue value):
    new_props = cProperties()
    new_props.load_from_value(value)
    return new_props


cdef class cProperties(StructBase):

    cdef c_amqp_definitions.PROPERTIES_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_amqp_definitions.properties_create()
        self._validate()

    def __dealloc__(self):
        _logger.debug("Deallocating cProperties")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                _logger.debug("Destroying cProperties")
                c_amqp_definitions.properties_destroy(self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
            self._c_value = <c_amqp_definitions.PROPERTIES_HANDLE>NULL

    cdef wrap(self, c_amqp_definitions.PROPERTIES_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    cdef load_from_value(self, AMQPValue value):
        self.destroy()
        if c_amqp_definitions.amqpvalue_get_properties(value._c_value, &self._c_value) != 0:
            self._value_error()
        self._validate()

    cdef get_properties(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_amqp_definitions.amqpvalue_create_properties(self._c_value)
        if <void*>_value is NULL:
            return None
        return value_factory(_value)

    cpdef clone(self):
        cdef c_amqp_definitions.PROPERTIES_HANDLE value
        value = c_amqp_definitions.properties_clone(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        new_obj = cProperties()
        new_obj.wrap(value)
        return new_obj

    @property
    def message_id(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.properties_get_message_id(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            cloned = c_amqpvalue.amqpvalue_clone(_value)
            if <void*>cloned == NULL:
                self._value_error()
            return value_factory(cloned)
        else:
            return None

    @message_id.setter
    def message_id(self, AMQPValue value):
        if c_amqp_definitions.properties_set_message_id(
            self._c_value, value._c_value) != 0:
                self._value_error("Could not set 'message_id'.")

    @property
    def user_id(self):
        cdef c_amqpvalue.amqp_binary _binary
        if c_amqp_definitions.properties_get_user_id(self._c_value, &_binary) == 0:
            bytes_value = <char*>_binary.bytes
            return bytes_value[:_binary.length]
        else:
            return None

    @user_id.setter
    def user_id(self, AMQPValue value):
        cdef c_amqpvalue.amqp_binary _binary
        if c_amqpvalue.amqpvalue_get_binary(value._c_value, &_binary) == 0:
            if c_amqp_definitions.properties_set_user_id(self._c_value, _binary) != 0:
                self._value_error("Could not set 'user_id'.")
        else:
            self._value_error("Could not set 'user_id'.")

    @property
    def to(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.properties_get_to(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            cloned = c_amqpvalue.amqpvalue_clone(_value)
            if <void*>cloned == NULL:
                self._value_error()
            return value_factory(cloned)
        else:
            return None

    @to.setter
    def to(self, AMQPValue value):
        if c_amqp_definitions.properties_set_to(
            self._c_value, value._c_value) != 0:
                self._value_error("Could not set 'to'.")

    @property
    def subject(self):
        cdef char* _value
        if c_amqp_definitions.properties_get_subject(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @subject.setter
    def subject(self, char* value):
        if c_amqp_definitions.properties_set_subject(
            self._c_value, value) != 0:
                self._value_error("Could not set 'subject'.")

    @property
    def reply_to(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.properties_get_reply_to(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            cloned = c_amqpvalue.amqpvalue_clone(_value)
            if <void*>cloned == NULL:
                self._value_error()
            return value_factory(cloned)
        else:
            return None

    @reply_to.setter
    def reply_to(self, AMQPValue value):
        if c_amqp_definitions.properties_set_reply_to(
            self._c_value, value._c_value) != 0:
                self._value_error("Could not set 'reply_to'.")

    @property
    def correlation_id(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_amqp_definitions.properties_get_correlation_id(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            cloned = c_amqpvalue.amqpvalue_clone(_value)
            if <void*>cloned == NULL:
                self._value_error()
            return value_factory(cloned)
        else:
            return None

    @correlation_id.setter
    def correlation_id(self, AMQPValue value):
        if c_amqp_definitions.properties_set_correlation_id(
            self._c_value, value._c_value) != 0:
                self._value_error("Could not set 'correlation_id'.")

    @property
    def content_type(self):
        cdef char* _value
        if c_amqp_definitions.properties_get_content_type(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @content_type.setter
    def content_type(self, char* value):
        if c_amqp_definitions.properties_set_content_type(
            self._c_value, value) != 0:
                self._value_error("Could not set 'content_type'.")

    @property
    def content_encoding(self):
        cdef char* _value
        if c_amqp_definitions.properties_get_content_encoding(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @content_encoding.setter
    def content_encoding(self, char* value):
        if c_amqp_definitions.properties_set_content_encoding(
            self._c_value, value) != 0:
                self._value_error("Could not set 'content_encoding'.")

    @property
    def absolute_expiry_time(self):
        cdef c_amqpvalue.timestamp _value
        if c_amqp_definitions.properties_get_absolute_expiry_time(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @absolute_expiry_time.setter
    def absolute_expiry_time(self, c_amqpvalue.timestamp value):
        if c_amqp_definitions.properties_set_absolute_expiry_time(
            self._c_value, value) != 0:
                self._value_error("Could not set 'absolute_expiry_time'.")

    @property
    def creation_time(self):
        cdef c_amqpvalue.timestamp _value
        if c_amqp_definitions.properties_get_creation_time(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @creation_time.setter
    def creation_time(self, c_amqpvalue.timestamp value):
        if c_amqp_definitions.properties_set_creation_time(
            self._c_value, value) != 0:
                self._value_error("Could not set 'create_time'.")

    @property
    def group_id(self):
        cdef const char* _value
        if c_amqp_definitions.properties_get_group_id(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @group_id.setter
    def group_id(self, const char* value):
        if c_amqp_definitions.properties_set_group_id(
            self._c_value, value) != 0:
                self._value_error("Could not set 'group_id'.")

    @property
    def group_sequence(self):
        cdef c_amqp_definitions.sequence_no _value
        if c_amqp_definitions.properties_get_group_sequence(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @group_sequence.setter
    def group_sequence(self, c_amqp_definitions.sequence_no value):
        if c_amqp_definitions.properties_set_group_sequence(
            self._c_value, value) != 0:
                self._value_error("Could not set 'group_Sequence'.")

    @property
    def reply_to_group_id(self):
        cdef char* _value
        if c_amqp_definitions.properties_get_reply_to_group_id(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            return None

    @reply_to_group_id.setter
    def reply_to_group_id(self, char* value):
        if c_amqp_definitions.properties_set_reply_to_group_id(
            self._c_value, value) != 0:
                self._value_error("Could not set 'reply_to_group_id'.")
