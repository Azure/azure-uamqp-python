#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqpvalue
cimport c_amqp_definitions


cdef extern from "azure_uamqp_c/messaging.h":

    c_amqpvalue.AMQP_VALUE messaging_create_source(const char* address)
    c_amqpvalue.AMQP_VALUE messaging_create_target(const char* address)

    c_amqpvalue.AMQP_VALUE messaging_delivery_received(stdint.uint32_t section_number, stdint.uint64_t section_offset) nogil
    c_amqpvalue.AMQP_VALUE messaging_delivery_accepted() nogil
    c_amqpvalue.AMQP_VALUE messaging_delivery_rejected(const char* error_condition, const char* error_description, c_amqp_definitions.fields error_info) nogil
    c_amqpvalue.AMQP_VALUE messaging_delivery_released() nogil
    c_amqpvalue.AMQP_VALUE messaging_delivery_modified(bint delivery_failed, bint undeliverable_here, c_amqp_definitions.fields message_annotations) nogil


cdef extern from "azure_uamqp_c/message.h":

    cdef enum MESSAGE_BODY_TYPE_TAG:
        MESSAGE_BODY_TYPE_NONE,
        MESSAGE_BODY_TYPE_DATA,
        MESSAGE_BODY_TYPE_SEQUENCE,
        MESSAGE_BODY_TYPE_VALUE,

    ctypedef struct MESSAGE_HANDLE:
        pass

    cdef struct BINARY_DATA_TAG:
        const unsigned char* bytes;
        size_t length;

    ctypedef BINARY_DATA_TAG BINARY_DATA

    MESSAGE_HANDLE message_create()
    MESSAGE_HANDLE message_clone(MESSAGE_HANDLE source_message)
    void message_destroy(MESSAGE_HANDLE message)
    int message_set_header(MESSAGE_HANDLE message, c_amqp_definitions.HEADER_HANDLE message_header)
    int message_get_header(MESSAGE_HANDLE message, c_amqp_definitions.HEADER_HANDLE* message_header)
    int message_set_delivery_annotations(MESSAGE_HANDLE message, c_amqp_definitions.delivery_annotations annotations)
    int message_get_delivery_annotations(MESSAGE_HANDLE message, c_amqp_definitions.delivery_annotations* annotations)
    int message_set_message_annotations(MESSAGE_HANDLE message, c_amqp_definitions.message_annotations annotations)
    int message_get_message_annotations(MESSAGE_HANDLE message, c_amqp_definitions.message_annotations* annotations)
    int message_set_properties(MESSAGE_HANDLE message, c_amqp_definitions.PROPERTIES_HANDLE properties)
    int message_get_properties(MESSAGE_HANDLE message, c_amqp_definitions.PROPERTIES_HANDLE* properties)
    int message_set_application_properties(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE application_properties)
    int message_get_application_properties(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE* application_properties)
    int message_set_footer(MESSAGE_HANDLE message, c_amqp_definitions.annotations footer)
    int message_get_footer(MESSAGE_HANDLE message, c_amqp_definitions.annotations* footer)
    
    int message_add_body_amqp_data(MESSAGE_HANDLE message, BINARY_DATA amqp_data)
    int message_get_body_amqp_data_in_place(MESSAGE_HANDLE message, size_t index, BINARY_DATA* amqp_data)
    int message_get_body_amqp_data_count(MESSAGE_HANDLE message, size_t* count)

    int message_set_body_amqp_value(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE body_amqp_value)
    int message_get_body_amqp_value_in_place(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE* body_amqp_value)

    int message_add_body_amqp_sequence(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE sequence)
    int message_get_body_amqp_sequence_in_place(MESSAGE_HANDLE message, size_t index, c_amqpvalue.AMQP_VALUE* sequence)
    int message_get_body_amqp_sequence_count(MESSAGE_HANDLE message, size_t* count)

    int message_get_body_type(MESSAGE_HANDLE message, MESSAGE_BODY_TYPE_TAG* body_type)
    int message_set_message_format(MESSAGE_HANDLE message, stdint.uint32_t message_format)
    int message_get_message_format(MESSAGE_HANDLE message, stdint.uint32_t* message_format)
    int message_get_delivery_tag(MESSAGE_HANDLE message, c_amqpvalue.AMQP_VALUE* delivery_tag)



