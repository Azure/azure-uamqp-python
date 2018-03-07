#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
from enum import Enum
import logging

# C imports
from libc cimport stdint

cimport c_message
cimport c_amqp_definitions
cimport c_amqpvalue


_logger = logging.getLogger(__name__)


class MessageBodyType(Enum):
    NoneType = c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_NONE
    DataType = c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_DATA
    SequenceType = c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_SEQUENCE
    ValueType = c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_VALUE


cdef message_factory(c_message.MESSAGE_HANDLE value):
    new_message = cMessage()
    new_message.wrap(value)
    return new_message


cpdef create_message():
    new_message = cMessage()
    new_message.create()
    return new_message


cdef class cMessage(StructBase):

    cdef c_message.MESSAGE_HANDLE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating {}".format(self.__class__.__name__))
        self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destorying {}".format(self.__class__.__name__))
            c_message.message_destroy(self._c_value)
            self._c_value = <c_message.MESSAGE_HANDLE>NULL

    cdef wrap(self, c_message.MESSAGE_HANDLE value):
        self.destroy()
        self._c_value = value
        self._create()

    cdef create(self):
        self.destroy()
        self._c_value = c_message.message_create()
        self._create()

    cpdef clone(self):
        cdef c_message.MESSAGE_HANDLE value
        value = c_message.message_clone(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        return message_factory(value)

    @property
    def header(self):
        cdef c_amqp_definitions.HEADER_HANDLE value
        if c_message.message_get_header(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cHeader()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @header.setter
    def header(self, cHeader value):
        if c_message.message_set_header(
            self._c_value, <c_amqp_definitions.HEADER_HANDLE>value._c_value) != 0:
                self._value_error()

    @property
    def delivery_annotations(self):
        cdef c_amqp_definitions.delivery_annotations value
        if c_message.message_get_delivery_annotations(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cDeliveryAnnotations()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @delivery_annotations.setter
    def delivery_annotations(self, cDeliveryAnnotations value):
        if c_message.message_set_delivery_annotations(
            self._c_value, <c_amqp_definitions.delivery_annotations>value._c_value) != 0:
                self._value_error()

    @property
    def message_annotations(self):
        cdef c_amqp_definitions.message_annotations value
        if c_message.message_get_message_annotations(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cMessageAnnotations()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @message_annotations.setter
    def message_annotations(self, cMessageAnnotations value):
        if c_message.message_set_message_annotations(
            self._c_value, <c_amqp_definitions.message_annotations>value._c_value) != 0:
                self._value_error()

    @property
    def properties(self):
        cdef c_amqp_definitions.PROPERTIES_HANDLE value
        if c_message.message_get_properties(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cProperties()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @properties.setter
    def properties(self, cProperties value):
        if value is None:  # TODO: We should do this throughout
            if c_message.message_set_properties(
                self._c_value, <c_amqp_definitions.PROPERTIES_HANDLE>NULL) != 0:
                    self._value_error()
        if c_message.message_set_properties(
            self._c_value, <c_amqp_definitions.PROPERTIES_HANDLE>value._c_value) != 0:
                self._value_error()

    @property
    def application_properties(self):
        cdef c_amqpvalue.AMQP_VALUE value
        if c_message.message_get_application_properties(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cApplicationProperties()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @application_properties.setter
    def application_properties(self, cApplicationProperties value):
        if c_message.message_set_application_properties(
            self._c_value, <c_amqpvalue.AMQP_VALUE>value._c_value) != 0:
                self._value_error()

    @property
    def footer(self):
        cdef c_amqp_definitions.annotations value
        if c_message.message_get_footer(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            new_obj = cFooter()
            new_obj.wrap(value)
            return new_obj
        else:
            self._value_error()

    @footer.setter
    def footer(self, cFooter value):
        if c_message.message_set_footer(
            self._c_value, <c_amqp_definitions.annotations>value._c_value) != 0:
                self._value_error()

    @property
    def body_type(self):
        cdef c_message.MESSAGE_BODY_TYPE_TAG value
        if c_message.message_get_body_type(self._c_value, &value) == 0:
            return MessageBodyType(value)
        else:
            self._value_error()

    @property
    def message_format(self):
        cdef stdint.uint32_t value
        if c_message.message_get_message_format(self._c_value, &value) == 0:
            return value
        else:
            self._value_error()

    @message_format.setter
    def message_format(self, stdint.uint32_t value):
        if c_message.message_set_message_format(self._c_value, value) != 0:
                self._value_error()

    cpdef add_body_data(self, bytes value):
        cdef c_message.BINARY_DATA _binary
        length = len(value)
        bytes = value[:length]
        _binary.length = length
        _binary.bytes = bytes
        if c_message.message_add_body_amqp_data(self._c_value, _binary) != 0:
            self._value_error()

    cpdef get_body_data(self, size_t index):
        cdef c_message.BINARY_DATA _value
        if c_message.message_get_body_amqp_data_in_place(self._c_value, index, &_value) == 0:
            return _value.bytes[:_value.length]
        else:
            self._value_error()

    cpdef count_body_data(self):
        cdef size_t body_count
        if c_message.message_get_body_amqp_data_count(self._c_value, &body_count) == 0:
            return body_count
        else:
            self._value_error()

    cpdef set_body_value(self, AMQPValue value):
        if c_message.message_set_body_amqp_value(self._c_value, <c_amqpvalue.AMQP_VALUE>value._c_value) != 0:
            self._value_error()

    cpdef get_body_value(self):
        cdef c_amqpvalue.AMQP_VALUE _value
        if c_message.message_get_body_amqp_value_in_place(self._c_value, &_value) == 0:
            return value_factory(_value)
        else:
            self._value_error()

    cpdef add_body_sequence(self, AMQPValue sequence):
        if c_message.message_add_body_amqp_sequence(self._c_value, <c_amqpvalue.AMQP_VALUE>sequence._c_value) != 0:
            self._value_error()

    cpdef get_body_sequence(self, size_t index):
        cdef c_amqpvalue.AMQP_VALUE _value
        if c_message.message_get_body_amqp_sequence_in_place(self._c_value, index, &_value) == 0:
            return value_factory(_value)
        else:
            self._value_error()

    cpdef count_body_sequence(self):
        cdef size_t body_count
        if c_message.message_get_body_amqp_sequence_count(self._c_value, &body_count) == 0:
            return body_count
        else:
            self._value_error()


cdef class Messaging:

    @staticmethod
    def create_source(const char* address):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_create_source(address)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for messaging source.")
        return value_factory(_value)

    @staticmethod
    def create_target(const char* address):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_create_target(address)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for messaging target.")
        return value_factory(_value)

    @staticmethod
    def delivery_received(stdint.uint32_t section_number, stdint.uint64_t section_offset):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_received(section_number, section_offset)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for received delivery.")
        return value_factory(_value)

    @staticmethod
    def delivery_accepted():
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_accepted()
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for accepted delivery.")
        return value_factory(_value)

    @staticmethod
    def delivery_rejected(const char* error_condition, const char* error_description):
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_rejected(error_condition, error_description)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for rejected delivery.")
        return value_factory(_value)

    @staticmethod
    def delivery_released():
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_released()
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for released delivery.")
        return value_factory(_value)

    @staticmethod
    def delivery_modified(bint delivery_failed, bint undeliverable_here, cFields message_annotations):
        _logger.debug("delivery modified: {} {}".format(delivery_failed, undeliverable_here))
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_modified(delivery_failed, undeliverable_here, <c_amqp_definitions.fields>message_annotations._c_value)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for modified delivery.")
        return value_factory(_value)


cpdef size_t get_encoded_message_size(cMessage message):

        cdef c_message.MESSAGE_HANDLE c_msg
        c_msg = c_message.message_clone(<c_message.MESSAGE_HANDLE>message._c_value)
        if <void*>c_msg == NULL:
            raise MemoryError("Unable to clone cMessage.")

        cdef c_message.MESSAGE_BODY_TYPE message_body_type
        cdef c_amqp_definitions.HEADER_HANDLE header
        cdef c_amqpvalue.AMQP_VALUE header_amqp_value
        cdef c_amqp_definitions.PROPERTIES_HANDLE properties
        cdef c_amqpvalue.AMQP_VALUE properties_amqp_value
        cdef c_amqpvalue.AMQP_VALUE application_properties
        cdef c_amqpvalue.AMQP_VALUE application_properties_value
        cdef c_amqpvalue.AMQP_VALUE body_amqp_value
        cdef c_amqpvalue.AMQP_VALUE msg_annotations
        cdef size_t encoded_size
        cdef size_t total_encoded_size = 0
        cdef size_t body_data_count = 0

        # message header
        if c_message.message_get_header(c_msg, &header) == 0 and <void*>header != NULL:
            header_amqp_value = c_amqp_definitions.amqpvalue_create_header(header)
            if <void*>header_amqp_value == NULL:
                _logger.debug("Cannot create header AMQP value")
                raise MemoryError("Cannot get cMessage header.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(header_amqp_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain header encoded size")
                    raise ValueError("Cannot obtain header encoded size")
                else:
                    total_encoded_size += encoded_size

        # message annotations
        if c_message.message_get_message_annotations(c_msg, &msg_annotations) == 0 and <void*>msg_annotations != NULL:
            if c_amqpvalue.amqpvalue_get_encoded_size(msg_annotations, &encoded_size) != 0:
                _logger.debug("Cannot obtain message annotations encoded size")
                raise ValueError("Cannot obtain message annotations encoded size")
            else:
                total_encoded_size += encoded_size

        # properties
        if c_message.message_get_properties(c_msg, &properties) == 0 and <void*>properties != NULL:
            properties_amqp_value = c_amqp_definitions.amqpvalue_create_properties(properties)
            if <void*>properties_amqp_value == NULL:
                _logger.debug("Cannot create properties AMQP value")
                raise MemoryError("Cannot get cMessage properties.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(properties_amqp_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain message properties encoded size")
                    raise ValueError("Cannot obtain message properties encoded size")
                else:
                    total_encoded_size += encoded_size

        # application properties
        if c_message.message_get_application_properties(c_msg, &application_properties) == 0 and <void*>application_properties != NULL:
            application_properties_value = c_amqp_definitions.amqpvalue_create_application_properties(application_properties)
            if <void*>application_properties_value == NULL:
                _logger.debug("Cannot create application properties AMQP value")
                raise MemoryError("Cannot get cMessage application properties.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(application_properties_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain application properties encoded size")
                    raise ValueError("Cannot obtain application properties encoded size")
                else:
                    total_encoded_size += encoded_size

        return total_encoded_size