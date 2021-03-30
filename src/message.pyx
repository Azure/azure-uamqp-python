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
        _logger.debug("Deallocating cMessage")
        self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                _logger.debug("Destroying cMessage")
                c_message.message_destroy(self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
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
        if value is None:
            if c_message.message_set_header(
                self._c_value, <c_amqp_definitions.HEADER_HANDLE>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_header(
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
        if value is None:
            if c_message.message_set_delivery_annotations(
                self._c_value, <c_amqp_definitions.delivery_annotations>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_delivery_annotations(
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
        if value is None:
            if c_message.message_set_message_annotations(
                self._c_value, <c_amqp_definitions.message_annotations>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_message_annotations(
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
        if value is None:
            if c_message.message_set_properties(
                self._c_value, <c_amqp_definitions.PROPERTIES_HANDLE>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_properties(
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
    def application_properties(self, AMQPValue value):
        if value is None:
            if c_message.message_set_application_properties(
                self._c_value, <c_amqpvalue.AMQP_VALUE>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_application_properties(
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
        if value is None:
            if c_message.message_set_footer(
                self._c_value, <c_amqp_definitions.annotations>NULL) != 0:
                    self._value_error()
        elif c_message.message_set_footer(
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

    @property
    def delivery_tag(self):
        cdef c_amqpvalue.AMQP_VALUE value
        if c_message.message_get_delivery_tag(self._c_value, &value) == 0:
            if <void*>value == NULL:
                return None
            return value_factory(value)
        else:
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
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_message.message_get_body_amqp_value_in_place(self._c_value, &_value) != 0:
            self._value_error()
        cloned = c_amqpvalue.amqpvalue_clone(_value)
        if <void*>cloned == NULL:
            self._value_error()
        return value_factory(cloned)

    cpdef add_body_sequence(self, AMQPValue sequence):
        if c_message.message_add_body_amqp_sequence(self._c_value, <c_amqpvalue.AMQP_VALUE>sequence._c_value) != 0:
            self._value_error()

    cpdef get_body_sequence(self, size_t index):
        cdef c_amqpvalue.AMQP_VALUE _value
        cdef c_amqpvalue.AMQP_VALUE cloned
        if c_message.message_get_body_amqp_sequence_in_place(self._c_value, index, &_value) != 0:
            self._value_error()
        cloned = c_amqpvalue.amqpvalue_clone(_value)
        if <void*>cloned == NULL:
            self._value_error()
        return value_factory(cloned)

    cpdef count_body_sequence(self):
        cdef size_t body_count
        if c_message.message_get_body_amqp_sequence_count(self._c_value, &body_count) == 0:
            return body_count
        else:
            self._value_error()


cdef class Messaging(object):

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
    def delivery_rejected(const char* error_condition, const char* error_description, cFields error_info=None):
        cdef c_amqpvalue.AMQP_VALUE _value

        if error_info is not None:
            delivery_fields = <c_amqp_definitions.fields>error_info._c_value
        else:
            delivery_fields = <c_amqp_definitions.fields>NULL

        _value = c_message.messaging_delivery_rejected(error_condition, error_description, delivery_fields)
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
        _logger.debug("delivery modified: %r %r", delivery_failed, undeliverable_here)
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = c_message.messaging_delivery_modified(delivery_failed, undeliverable_here, <c_amqp_definitions.fields>message_annotations._c_value)
        if <void*>_value == NULL:
            raise MemoryError("Failed to allocate memory for modified delivery.")
        return value_factory(_value)


cdef void destroy_amqp_objects_in_get_encoded_message_size(c_amqp_definitions.HEADER_HANDLE header,
    c_amqpvalue.AMQP_VALUE header_amqp_value, c_amqpvalue.AMQP_VALUE msg_annotations,
    c_amqpvalue.AMQP_VALUE footer, c_amqpvalue.AMQP_VALUE delivery_annotations,
    c_amqp_definitions.PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE properties_amqp_value,
    c_amqpvalue.AMQP_VALUE application_properties, c_amqpvalue.AMQP_VALUE application_properties_value,
    c_amqpvalue.AMQP_VALUE body_amqp_value):

    if <void*>header != NULL:
        c_amqp_definitions.header_destroy(header)

    if <void*>header_amqp_value != NULL:
        c_amqpvalue.amqpvalue_destroy(header_amqp_value)

    if <void*>msg_annotations != NULL:
        c_amqpvalue.amqpvalue_destroy(msg_annotations)

    if <void*>footer != NULL:
        c_amqpvalue.amqpvalue_destroy(footer)

    if <void*>delivery_annotations != NULL:
        c_amqpvalue.amqpvalue_destroy(delivery_annotations)

    if <void*>properties != NULL:
        c_amqp_definitions.properties_destroy(properties)

    if <void*>properties_amqp_value != NULL:
        c_amqpvalue.amqpvalue_destroy(properties_amqp_value)

    if <void*>application_properties != NULL:
        c_amqpvalue.amqpvalue_destroy(application_properties)

    if <void*>application_properties_value != NULL:
        c_amqpvalue.amqpvalue_destroy(application_properties_value)

    if <void*>body_amqp_value != NULL:
        c_amqpvalue.amqpvalue_destroy(body_amqp_value)


cpdef size_t get_encoded_message_size(cMessage message, encoded_data):

        cdef c_message.MESSAGE_HANDLE c_msg
        c_msg = <c_message.MESSAGE_HANDLE>message._c_value

        cdef c_message.MESSAGE_BODY_TYPE_TAG message_body_type
        cdef c_amqp_definitions.message_format message_format
        cdef c_amqp_definitions.HEADER_HANDLE header = <c_amqp_definitions.HEADER_HANDLE>NULL
        cdef c_amqpvalue.AMQP_VALUE header_amqp_value = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqp_definitions.PROPERTIES_HANDLE properties = <c_amqp_definitions.PROPERTIES_HANDLE>NULL
        cdef c_amqpvalue.AMQP_VALUE properties_amqp_value = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE application_properties = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE application_properties_value = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE body_amqp_value = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE msg_annotations = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE footer = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE delivery_annotations = <c_amqpvalue.AMQP_VALUE>NULL
        cdef c_amqpvalue.AMQP_VALUE message_body_amqp_value
        cdef c_amqpvalue.AMQP_VALUE message_body_amqp_sequence
        cdef c_message.BINARY_DATA binary_data
        cdef c_amqpvalue.AMQP_VALUE body_amqp_data
        cdef c_amqpvalue.AMQP_VALUE body_amqp_sequence
        cdef c_amqpvalue.amqp_binary binary_value
        cdef size_t encoded_size
        cdef size_t total_encoded_size = 0
        cdef size_t body_data_count = 0
        cdef size_t body_sequence_count = 0

        # message format
        if (c_message.message_get_body_type(c_msg, &message_body_type) != 0) or (c_message.message_get_message_format(c_msg, &message_format) != 0):
            raise ValueError("Failure getting message body type and/or message format")

        # message header
        if c_message.message_get_header(c_msg, &header) == 0 and <void*>header != NULL:
            header_amqp_value = c_amqp_definitions.amqpvalue_create_header(header)
            if <void*>header_amqp_value == NULL:
                _logger.debug("Cannot create header AMQP value")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise MemoryError("Cannot get cMessage header.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(header_amqp_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain header encoded size")
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot obtain header encoded size")
                else:
                    total_encoded_size += encoded_size

        # message annotations
        if c_message.message_get_message_annotations(c_msg, &msg_annotations) == 0 and <void*>msg_annotations != NULL:
            if c_amqpvalue.amqpvalue_get_encoded_size(msg_annotations, &encoded_size) != 0:
                _logger.debug("Cannot obtain message annotations encoded size")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot obtain message annotations encoded size")
            else:
                total_encoded_size += encoded_size

        # properties
        if c_message.message_get_properties(c_msg, &properties) == 0 and <void*>properties != NULL:
            properties_amqp_value = c_amqp_definitions.amqpvalue_create_properties(properties)
            if <void*>properties_amqp_value == NULL:
                _logger.debug("Cannot create properties AMQP value")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise MemoryError("Cannot get cMessage properties.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(properties_amqp_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain message properties encoded size")
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot obtain message properties encoded size")
                else:
                    total_encoded_size += encoded_size

        # application properties
        if c_message.message_get_application_properties(c_msg, &application_properties) == 0 and <void*>application_properties != NULL:
            application_properties_value = c_amqp_definitions.amqpvalue_create_application_properties(application_properties)
            if <void*>application_properties_value == NULL:
                _logger.debug("Cannot create application properties AMQP value")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise MemoryError("Cannot get cMessage application properties.")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(application_properties_value, &encoded_size) != 0:
                    _logger.debug("Cannot obtain application properties encoded size")
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot obtain application properties encoded size")
                else:
                    total_encoded_size += encoded_size

        # footer
        if c_message.message_get_footer(c_msg, &footer) == 0 and <void*>footer != NULL:
            if c_amqpvalue.amqpvalue_get_encoded_size(footer, &encoded_size) != 0:
                _logger.debug("Cannot obtain footer encoded size")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot obtain footer encoded size")
            else:
                total_encoded_size += encoded_size

        # delivery annotations
        if c_message.message_get_delivery_annotations(c_msg, &delivery_annotations) == 0 and <void*>delivery_annotations != NULL:
            if c_amqpvalue.amqpvalue_get_encoded_size(delivery_annotations, &encoded_size) != 0:
                _logger.debug("Cannot obtain delivery annotations encoded size")
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot obtain delivery annotations encoded size")
            else:
                total_encoded_size += encoded_size

        # value body
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_VALUE:
            if c_message.message_get_body_amqp_value_in_place(c_msg, &message_body_amqp_value) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot obtain AMQP value from body")
            body_amqp_value = c_amqp_definitions.amqpvalue_create_amqp_value(message_body_amqp_value)
            if <void*>body_amqp_value == NULL:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise MemoryError("Cannot create body AMQP value")
            else:
                if c_amqpvalue.amqpvalue_get_encoded_size(body_amqp_value, &encoded_size) != 0:
                    _logger.debug("Cannot get body AMQP value encoded size")
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot get body AMQP value encoded size")
                else:
                    total_encoded_size += encoded_size

        # data body
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_DATA:
            if c_message.message_get_body_amqp_data_count(c_msg, &body_data_count) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot get body AMQP data count")
            if body_data_count == 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Body data count is zero")
            for i in range(body_data_count):
                if c_message.message_get_body_amqp_data_in_place(c_msg, i, &binary_data) != 0:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot get body AMQP data {}".format(i))

                binary_value.bytes = binary_data.bytes
                binary_value.length = <stdint.uint32_t>binary_data.length
                body_amqp_data = c_amqp_definitions.amqpvalue_create_data(binary_value)
                if <void*>body_amqp_data == NULL:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise MemoryError("Cannot create body AMQP data")
                else:
                    if c_amqpvalue.amqpvalue_get_encoded_size(body_amqp_data, &encoded_size) != 0:
                        _logger.debug("Cannot get body AMQP data encoded size")
                        destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                            properties, properties_amqp_value, application_properties, application_properties_value,
                            body_amqp_value)
                        c_amqpvalue.amqpvalue_destroy(body_amqp_data)
                        raise ValueError("Cannot get body AMQP data encoded size")
                    else:
                        total_encoded_size += encoded_size
                    c_amqpvalue.amqpvalue_destroy(body_amqp_data)

        # sequence body
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_SEQUENCE:
            if c_message.message_get_body_amqp_sequence_count(c_msg, &body_sequence_count) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot get body AMQP sequence count")
            if body_sequence_count == 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Body sequence count is zero")
            for i in range(body_sequence_count):
                if c_message.message_get_body_amqp_sequence_in_place(c_msg, i, &message_body_amqp_sequence) != 0:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot get body AMQP sequence {}".format(i))

                body_amqp_sequence = c_amqp_definitions.amqpvalue_create_amqp_sequence(message_body_amqp_sequence);
                if <void*> body_amqp_sequence == NULL:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise MemoryError("Cannot create body AMQP sequence")
                else:
                    if c_amqpvalue.amqpvalue_get_encoded_size(body_amqp_sequence, &encoded_size) != 0:
                        _logger.debug("Cannot get body AMQP sequence encoded size")
                        destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                            properties, properties_amqp_value, application_properties, application_properties_value,
                            body_amqp_value)
                        c_amqpvalue.amqpvalue_destroy(body_amqp_sequence)
                        raise ValueError("Cannot get body AMQP sequence encoded size")
                    else:
                        total_encoded_size += encoded_size
                    c_amqpvalue.amqpvalue_destroy(body_amqp_sequence)

        # encode
        if <void*>header != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    header_amqp_value,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode header value")
        if <void*>msg_annotations != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    msg_annotations,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode message annotations value")
        if <void*>properties != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    properties_amqp_value,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode message properties value")
        if <void*>application_properties != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    application_properties_value,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode application properties value")
        if <void*>footer != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    footer,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode footer value")
        if <void*>delivery_annotations != NULL:
            if c_amqpvalue.amqpvalue_encode(
                    delivery_annotations,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode delivery annotations value")
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_VALUE:
            if c_amqpvalue.amqpvalue_encode(
                    body_amqp_value,
                    <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                    <void*>encoded_data) != 0:
                destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                    properties, properties_amqp_value, application_properties, application_properties_value,
                    body_amqp_value)
                raise ValueError("Cannot encode body AMQP value")
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_DATA:
            for i in range(body_data_count):
                if c_message.message_get_body_amqp_data_in_place(c_msg, i, &binary_data) != 0:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot get body AMQP data {}".format(i))

                binary_value.bytes = binary_data.bytes
                binary_value.length = <stdint.uint32_t>binary_data.length
                body_amqp_data = c_amqp_definitions.amqpvalue_create_data(binary_value)
                if <void*>body_amqp_data == NULL:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise MemoryError("Cannot create body AMQP data")
                else:
                    if c_amqpvalue.amqpvalue_encode(
                            body_amqp_data,
                            <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                            <void*>encoded_data) != 0:
                        destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                            properties, properties_amqp_value, application_properties, application_properties_value,
                            body_amqp_value)
                        c_amqpvalue.amqpvalue_destroy(body_amqp_data)
                        raise ValueError("Cannot encode body AMQP value")
                    c_amqpvalue.amqpvalue_destroy(body_amqp_data)
        if message_body_type == c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_SEQUENCE:
            for i in range(body_sequence_count):
                if c_message.message_get_body_amqp_sequence_in_place(c_msg, i, &message_body_amqp_sequence) != 0:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise ValueError("Cannot get body AMQP sequence {}".format(i))

                body_amqp_sequence = c_amqp_definitions.amqpvalue_create_amqp_sequence(message_body_amqp_sequence);
                if <void*> body_amqp_sequence == NULL:
                    destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                        properties, properties_amqp_value, application_properties, application_properties_value,
                        body_amqp_value)
                    raise MemoryError("Cannot create body AMQP sequence")
                else:
                    if c_amqpvalue.amqpvalue_encode(
                            body_amqp_sequence,
                            <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                            <void*>encoded_data) != 0:
                        destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
                            properties, properties_amqp_value, application_properties, application_properties_value,
                            body_amqp_value)
                        c_amqpvalue.amqpvalue_destroy(body_amqp_sequence)
                        raise ValueError("Cannot get body AMQP sequence encoded size")
                    c_amqpvalue.amqpvalue_destroy(body_amqp_sequence)

        destroy_amqp_objects_in_get_encoded_message_size(header, header_amqp_value, msg_annotations, footer, delivery_annotations,
            properties, properties_amqp_value, application_properties, application_properties_value,
            body_amqp_value)

        return total_encoded_size


cdef class cMessageDecoder(object):

    cdef c_message.MESSAGE_HANDLE decoded_message
    cdef const char* decode_error

    def __cinit__(self):
        self.decoded_message = c_message.message_create()
        if <void*>self.decoded_message == NULL:
            raise MemoryError("Failed to create message decoder.")
        self.decode_error = <const char*>NULL

    def __dealloc__(self):
        _logger.debug("Deallocating cMessageDecoder")


cpdef cMessage decode_message(stdint.uint32_t payload_size, const unsigned char* payload_bytes):
    cdef c_amqpvalue.AMQPVALUE_DECODER_HANDLE amqpvalue_decoder
    cdef c_message.MESSAGE_HANDLE result
    message_decoder = cMessageDecoder()

    amqpvalue_decoder = c_amqpvalue.amqpvalue_decoder_create(<c_amqpvalue.ON_VALUE_DECODED>decode_message_data, <void*>message_decoder);
    if <void*>amqpvalue_decoder == NULL:
        raise MemoryError("Cannot create AMQP value decoder")
    else:
        if c_amqpvalue.amqpvalue_decode_bytes(amqpvalue_decoder, payload_bytes, payload_size) != 0:
            raise ValueError("Cannot decode bytes")
        else:
            if <void*>message_decoder.decode_error != NULL:
                raise ValueError(message_decoder.decode_error.decode('UTF-8'))
            else:
                result = message_decoder.decoded_message

        c_amqpvalue.amqpvalue_decoder_destroy(amqpvalue_decoder)
    return message_factory(result)


cdef void decode_message_data(void* context, c_amqpvalue.AMQP_VALUE decoded_value):
    message_decoder = <cMessageDecoder>context
    cdef c_message.MESSAGE_HANDLE decoded_message
    cdef c_amqpvalue.AMQP_VALUE descriptor
    cdef c_amqp_definitions.PROPERTIES_HANDLE properties
    cdef c_amqp_definitions.annotations delivery_annotations
    cdef c_amqp_definitions.annotations message_annotations
    cdef c_amqp_definitions.HEADER_HANDLE header
    cdef c_amqp_definitions.annotations footer
    cdef c_message.MESSAGE_BODY_TYPE_TAG body_type
    cdef c_amqpvalue.AMQP_VALUE body_amqp_value
    cdef c_amqpvalue.AMQP_VALUE body_data_value
    cdef c_amqp_definitions.data data_value
    cdef c_message.BINARY_DATA binary_data

    decoded_message = message_decoder.decoded_message
    descriptor = c_amqpvalue.amqpvalue_get_inplace_descriptor(decoded_value)

    if c_amqp_definitions.is_application_properties_type_by_descriptor(descriptor):
        if c_message.message_set_application_properties(decoded_message, decoded_value) != 0:
            message_decoder.decode_error = b"Error setting application properties on received message"

    elif c_amqp_definitions.is_properties_type_by_descriptor(descriptor):
        if c_amqp_definitions.amqpvalue_get_properties(decoded_value, &properties) != 0:
            message_decoder.decode_error = b"Error getting message properties"

        else:
            if c_message.message_set_properties(decoded_message, properties) != 0:
                message_decoder.decode_error = b"Error setting message properties on received message"
            c_amqp_definitions.properties_destroy(properties)

    elif c_amqp_definitions.is_delivery_annotations_type_by_descriptor(descriptor):
        delivery_annotations = c_amqpvalue.amqpvalue_get_inplace_described_value(decoded_value)
        if <void*>delivery_annotations == NULL:
            message_decoder.decode_error = b"Error getting delivery annotations"
        else:
            if c_message.message_set_delivery_annotations(decoded_message, delivery_annotations) != 0:
                message_decoder.decode_error = b"Error setting delivery annotations on received message"

    elif c_amqp_definitions.is_message_annotations_type_by_descriptor(descriptor):
        message_annotations = c_amqpvalue.amqpvalue_get_inplace_described_value(decoded_value)
        if <void*>message_annotations == NULL:
            message_decoder.decode_error = b"Error getting message annotations"
        else:
            if c_message.message_set_message_annotations(decoded_message, message_annotations) != 0:
                message_decoder.decode_error = b"Error setting message annotations on received message"

    elif c_amqp_definitions.is_header_type_by_descriptor(descriptor):
        if c_amqp_definitions.amqpvalue_get_header(decoded_value, &header) != 0:
            message_decoder.decode_error = b"Error getting message header"
        else:
            if c_message.message_set_header(decoded_message, header) != 0:
                message_decoder.decode_error = b"Error setting message header on received message"
            c_amqp_definitions.header_destroy(header)

    elif c_amqp_definitions.is_footer_type_by_descriptor(descriptor):
        footer = c_amqpvalue.amqpvalue_get_inplace_described_value(decoded_value);
        if <void*>footer == NULL:
            message_decoder.decode_error = b"Error getting message footer"
        else:
            if c_message.message_set_footer(decoded_message, footer) != 0:
                message_decoder.decode_error = b"Error setting message footer on received message"

    elif c_amqp_definitions.is_amqp_value_type_by_descriptor(descriptor):
        if c_message.message_get_body_type(decoded_message, &body_type) != 0:
            message_decoder.decode_error = b"Error getting message body type"

        else:
            if body_type != c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_NONE:
                message_decoder.decode_error = b"Body already set on received message"

            else:
                body_amqp_value = c_amqpvalue.amqpvalue_get_inplace_described_value(decoded_value)
                if <void*>body_amqp_value == NULL:
                    message_decoder.decode_error = b"Error getting body AMQP value"
                else:
                    if c_message.message_set_body_amqp_value(decoded_message, body_amqp_value) != 0:
                        message_decoder.decode_error = b"Error setting body AMQP value on received message"

    elif c_amqp_definitions.is_data_type_by_descriptor(descriptor):
        if c_message.message_get_body_type(decoded_message, &body_type) != 0:
            message_decoder.decode_error = b"Error getting message body type"

        else:
            if (body_type != c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_NONE) and (body_type != c_message.MESSAGE_BODY_TYPE_TAG.MESSAGE_BODY_TYPE_DATA):
                message_decoder.decode_error = b"Message body type already set to something different than AMQP DATA"

            else:
                body_data_value = c_amqpvalue.amqpvalue_get_inplace_described_value(decoded_value)
                if <void*>body_data_value == NULL:
                    message_decoder.decode_error = b"Error getting body DATA value"

                else:
                    if c_amqpvalue.amqpvalue_get_binary(body_data_value, &data_value) != 0:
                        message_decoder.decode_error = b"Error getting body DATA AMQP value"

                    else:
                        binary_data.bytes = <const unsigned char*>data_value.bytes
                        binary_data.length = data_value.length
                        if c_message.message_add_body_amqp_data(decoded_message, binary_data) != 0:
                            message_decoder.decode_error = b"Error adding body DATA to received message"
