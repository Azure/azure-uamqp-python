#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging
import copy

# C imports
from libc cimport stdint

cimport c_amqpvalue
cimport c_amqp_definitions
cimport c_utils


_logger = logging.getLogger(__name__)


cdef annotations_factory(c_amqpvalue.AMQP_VALUE value):
    try:
        wrapped = value_factory(value)
    except TypeError:
        return None
    if c_amqp_definitions.is_delivery_annotations_type_by_descriptor(<c_amqp_definitions.delivery_annotations>value):
        new_obj = create_delivery_annotations(wrapped)
    elif c_amqp_definitions.is_message_annotations_type_by_descriptor(<c_amqp_definitions.message_annotations>value):
        new_obj = create_message_annotations(wrapped)
    elif c_amqp_definitions.is_footer_type_by_descriptor(<c_amqp_definitions.footer>value):
        new_obj = create_footer(wrapped)
    else:
        new_obj = create_annotations(wrapped)
    return new_obj


cpdef create_annotations(AMQPValue value):
    annotations = cAnnotations()
    annotations.create(value)
    return annotations


cpdef create_application_properties(AMQPValue value):
    annotations = cApplicationProperties()
    annotations.create(value)
    return annotations


cpdef create_delivery_annotations(AMQPValue value):
    annotations = cDeliveryAnnotations()
    annotations.create(value)
    return annotations


cpdef create_message_annotations(AMQPValue value):
    annotations = cMessageAnnotations()
    annotations.create(value)
    return annotations


cpdef create_fields(AMQPValue value):
    annotations = cFields()
    annotations.create(value)
    return annotations


cpdef create_footer(AMQPValue value):
    annotations = cFooter()
    annotations.create(value)
    return annotations


cdef class cAnnotations(StructBase):

    cdef c_amqpvalue.AMQP_VALUE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating %r", self.__class__.__name__)
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                _logger.debug("Destroying %r", self.__class__.__name__)
                c_amqpvalue.amqpvalue_destroy(<c_amqpvalue.AMQP_VALUE>self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
            self._c_value = <c_amqpvalue.AMQP_VALUE>NULL

    cpdef clone(self):
        cdef c_amqp_definitions.annotations value
        value = c_amqpvalue.amqpvalue_clone(<c_amqpvalue.AMQP_VALUE>self._c_value)
        if <void*>value == NULL:
            self._value_error()
        amqp_value = value_factory(value)
        return cAnnotations(amqp_value)

    cpdef get_encoded_size(self):
        cdef size_t length
        if c_amqpvalue.amqpvalue_get_encoded_size(self._c_value, &length) != 0:
            self._value_error("Failed to get encoded size.")
        return length

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_annotations(<c_amqpvalue.AMQP_VALUE>value._c_value)
        self._validate()

    cdef wrap(self, c_amqp_definitions.annotations value):
        self.destroy()
        self._c_value = value
        self._validate()

    @property
    def value(self):
        try:
            return value_factory(self._c_value)
        except TypeError:
            return None

    @property
    def map(self):
        cdef c_amqpvalue.AMQP_VALUE unmapped
        cdef c_amqpvalue.AMQP_VALUE mapped
        unmapped = c_amqpvalue.amqpvalue_clone(<c_amqpvalue.AMQP_VALUE>self._c_value)
        if c_amqpvalue.amqpvalue_get_map(unmapped, &mapped) == 0:
            if <void*>mapped == NULL:
                return None
            return copy.deepcopy(value_factory(mapped).value)
        else:
            return None


cdef class cApplicationProperties(cAnnotations):

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_application_properties(
            <c_amqp_definitions.application_properties>value._c_value)
        self._validate()

    @property
    def map(self):
        cdef c_amqpvalue.AMQP_VALUE unmapped
        cdef c_amqpvalue.AMQP_VALUE mapped
        cdef c_amqpvalue.AMQP_VALUE unextracted
        cdef c_amqpvalue.AMQP_VALUE extracted
        unextracted = c_amqpvalue.amqpvalue_clone(<c_amqpvalue.AMQP_VALUE>self._c_value)
        extracted = c_amqpvalue.amqpvalue_get_inplace_described_value(unextracted)
        unmapped = c_amqpvalue.amqpvalue_clone(extracted)
        if <void*>unmapped == NULL:
            result = None
        elif c_amqpvalue.amqpvalue_get_map(unmapped, &mapped) == 0:
            if <void*>mapped == NULL:
                result = None
            else:
                result = copy.deepcopy(value_factory(mapped).value)
        else:
            result = None
        c_amqpvalue.amqpvalue_destroy(unextracted)
        return result


cdef class cDeliveryAnnotations(cAnnotations):

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_delivery_annotations(
            <c_amqp_definitions.delivery_annotations>value._c_value)
        self._validate()


cdef class cMessageAnnotations(cAnnotations):

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_message_annotations(
            <c_amqp_definitions.message_annotations>value._c_value)
        self._validate()


cdef class cFields(cAnnotations):

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_fields(<c_amqp_definitions.fields>value._c_value)
        self._validate()


cdef class cFooter(cAnnotations):

    cpdef create(self, AMQPValue value):
        self.destroy()
        self._c_value = c_amqp_definitions.amqpvalue_create_footer(<c_amqp_definitions.footer>value._c_value)
        self._validate()
