#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqpvalue


cdef extern from "azure_uamqp_c/amqp_definitions.h":

    ctypedef stdint.uint_fast32_t tickcounter_ms_t

    # role
    ctypedef bint role
    c_amqpvalue.AMQP_VALUE amqpvalue_create_role(role value)
    cdef bint role_sender
    cdef bint role_receiver
    #cdef c_amqpvalue.amqpvalue_get_boolean amqpvalue_get_role

    # sender-settle-mode
    ctypedef stdint.uint8_t sender_settle_mode
    c_amqpvalue.AMQP_VALUE amqpvalue_create_sender_settle_mode(sender_settle_mode value)
    cdef stdint.uint8_t sender_settle_mode_unsettled
    cdef stdint.uint8_t sender_settle_mode_settled
    cdef stdint.uint8_t sender_settle_mode_mixed
    #cdef amqpvalue_get_sender_settle_mode

    # receiver-settle-mode
    ctypedef stdint.uint8_t receiver_settle_mode
    c_amqpvalue.AMQP_VALUE amqpvalue_create_receiver_settle_mode(receiver_settle_mode value)
    cdef int receiver_settle_mode_first
    cdef int receiver_settle_mode_second
    #cdef amqpvalue_get_receiver_settle_mode

    # handle
    ctypedef stdint.uint32_t handle
    c_amqpvalue.AMQP_VALUE amqpvalue_create_handle(handle value)
    #cdef amqpvalue_get_handle
    # seconds
    ctypedef stdint.uint32_t seconds
    c_amqpvalue.AMQP_VALUE amqpvalue_create_seconds(seconds value)
    #cdef amqpvalue_get_seconds

    # milliseconds
    ctypedef stdint.uint32_t milliseconds
    c_amqpvalue.AMQP_VALUE amqpvalue_create_milliseconds(milliseconds value)
    #cdef amqpvalue_get_milliseconds

    # delivery-tag 
    ctypedef c_amqpvalue.amqp_binary delivery_tag
    c_amqpvalue.AMQP_VALUE amqpvalue_create_delivery_tag(delivery_tag value)
    #cdef amqpvalue_get_delivery_tag

    # sequence-no
    ctypedef stdint.uint32_t sequence_no
    c_amqpvalue.AMQP_VALUE amqpvalue_create_sequence_no(sequence_no value)
    #cdef amqpvalue_get_sequence_no

    # delivery-number
    ctypedef sequence_no delivery_number
    c_amqpvalue.AMQP_VALUE amqpvalue_create_delivery_number(delivery_number value)
    #cdef amqpvalue_get_delivery_number

    # transfer-number
    ctypedef sequence_no transfer_number
    c_amqpvalue.AMQP_VALUE amqpvalue_create_transfer_number(transfer_number value)
    #cdef amqpvalue_get_transfer_number

    # message-format
    ctypedef stdint.uint32_t message_format
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_format(message_format value)
    #cdef amqpvalue_get_message_format

    # ietf-language-tag
    ctypedef char* ietf_language_tag
    c_amqpvalue.AMQP_VALUE amqpvalue_create_ietf_language_tag(ietf_language_tag value)
    #cdef amqpvalue_get_ietf_language_tag

    # fields
    ctypedef c_amqpvalue.AMQP_VALUE fields
    c_amqpvalue.AMQP_VALUE amqpvalue_create_fields(c_amqpvalue.AMQP_VALUE value)
    #cdef fields_clone
    #cdef fields_destroy
    #cdef amqpvalue_get_fields

    # annotations
    ctypedef c_amqpvalue.AMQP_VALUE annotations
    c_amqpvalue.AMQP_VALUE amqpvalue_create_annotations(c_amqpvalue.AMQP_VALUE value)
    # cdef amqpvalue_get_annotations c_amqpvalue.amqpvalue_get_map  TODO


    # message-id-ulong
    ctypedef stdint.uint64_t message_id_ulong
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_id_ulong(message_id_ulong value)
    #cdef amqpvalue_get_message_id_ulong


    # message-id-uuid
    ctypedef c_amqpvalue.uuid message_id_uuid
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_id_uuid(message_id_uuid value)
    #cdef amqpvalue_get_message_id_uuid


    # message-id-binary
    ctypedef c_amqpvalue.amqp_binary message_id_binary
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_id_binary(message_id_binary value)
    #cdef amqpvalue_get_message_id_binary


    # message-id-string
    ctypedef char* message_id_string
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_id_string(message_id_string value)
    #cdef amqpvalue_get_message_id_string


    # address-string
    ctypedef char* address_string
    c_amqpvalue.AMQP_VALUE amqpvalue_create_address_string(address_string value)
    #cdef amqpvalue_get_address_string

    # error
    ctypedef struct ERROR_HANDLE:
        pass

    ERROR_HANDLE error_create(const char* condition_value)
    ERROR_HANDLE error_clone(ERROR_HANDLE value)
    void error_destroy(ERROR_HANDLE error)
    int error_get_condition(ERROR_HANDLE error, const char** condition_value)
    int error_set_condition(ERROR_HANDLE error, const char* condition_value)
    int error_get_description(ERROR_HANDLE error, const char** description_value)
    int error_set_description(ERROR_HANDLE error, const char* description_value)
    int error_get_info(ERROR_HANDLE error, fields* info_value)
    int error_set_info(ERROR_HANDLE error, fields info_value)

    # header
    ctypedef struct HEADER_HANDLE:
        pass

    HEADER_HANDLE header_create()
    HEADER_HANDLE header_clone(HEADER_HANDLE value)
    void header_destroy(HEADER_HANDLE header)
    bint is_header_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    int amqpvalue_get_header(c_amqpvalue.AMQP_VALUE value, HEADER_HANDLE* HEADER_handle)
    c_amqpvalue.AMQP_VALUE amqpvalue_create_header(HEADER_HANDLE header)
    int header_get_durable(HEADER_HANDLE header, bint* durable_value)
    int header_set_durable(HEADER_HANDLE header, bint durable_value)
    int header_get_priority(HEADER_HANDLE header, stdint.uint8_t* priority_value)
    int header_set_priority(HEADER_HANDLE header, stdint.uint8_t priority_value)
    int header_get_ttl(HEADER_HANDLE header, milliseconds* ttl_value)
    int header_set_ttl(HEADER_HANDLE header, milliseconds ttl_value)
    int header_get_first_acquirer(HEADER_HANDLE header, bint* first_acquirer_value)
    int header_set_first_acquirer(HEADER_HANDLE header, bint first_acquirer_value)
    int header_get_delivery_count(HEADER_HANDLE header, stdint.uint32_t* delivery_count_value)
    int header_set_delivery_count(HEADER_HANDLE header, stdint.uint32_t delivery_count_value)

    # delivery-annotations
    ctypedef annotations delivery_annotations
    c_amqpvalue.AMQP_VALUE amqpvalue_create_delivery_annotations(delivery_annotations value)
    bint is_delivery_annotations_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_delivery_annotations amqpvalue_get_annotations TODO

    # message-annotations
    ctypedef annotations message_annotations
    c_amqpvalue.AMQP_VALUE amqpvalue_create_message_annotations(message_annotations value)
    bint is_message_annotations_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_message_annotations amqpvalue_get_annotations TODO

    # application-properties
    ctypedef c_amqpvalue.AMQP_VALUE application_properties
    c_amqpvalue.AMQP_VALUE amqpvalue_create_application_properties(c_amqpvalue.AMQP_VALUE value)
    #cdef application_properties_clone
    #cdef application_properties_destroy
    bint is_application_properties_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_application_properties

    # data
    ctypedef c_amqpvalue.amqp_binary data
    c_amqpvalue.AMQP_VALUE amqpvalue_create_data(data value)
    bint is_data_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_data

    # amqp-sequence
    ctypedef c_amqpvalue.AMQP_VALUE amqp_sequence
    c_amqpvalue.AMQP_VALUE amqpvalue_create_amqp_sequence(c_amqpvalue.AMQP_VALUE value)
    #cdef amqp_sequence_clone
    #cdef amqp_sequence_destroy
    bint is_amqp_sequence_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_amqp_sequence

    # amqp-value
    ctypedef c_amqpvalue.AMQP_VALUE amqp_value
    c_amqpvalue.AMQP_VALUE amqpvalue_create_amqp_value(c_amqpvalue.AMQP_VALUE value)
    #cdef amqp_value_clone
    #cdef amqp_value_destroy
    bint is_amqp_value_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_amqp_value

    # footer
    ctypedef annotations footer
    c_amqpvalue.AMQP_VALUE amqpvalue_create_footer(footer value)
    bint is_footer_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    #cdef amqpvalue_get_footer

    # properties
    ctypedef struct PROPERTIES_HANDLE:
        pass
    PROPERTIES_HANDLE properties_create()
    PROPERTIES_HANDLE properties_clone(PROPERTIES_HANDLE value)
    void properties_destroy(PROPERTIES_HANDLE properties)
    bint is_properties_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    int amqpvalue_get_properties(c_amqpvalue.AMQP_VALUE value, PROPERTIES_HANDLE* PROPERTIES_handle)
    c_amqpvalue.AMQP_VALUE amqpvalue_create_properties(PROPERTIES_HANDLE properties)
    int properties_get_message_id(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE* message_id_value)
    int properties_set_message_id(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE message_id_value)
    int properties_get_user_id(PROPERTIES_HANDLE properties, c_amqpvalue.amqp_binary* user_id_value)
    int properties_set_user_id(PROPERTIES_HANDLE properties, c_amqpvalue.amqp_binary user_id_value)
    int properties_get_to(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE* to_value)
    int properties_set_to(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE to_value)
    int properties_get_subject(PROPERTIES_HANDLE properties, char** subject_value)
    int properties_set_subject(PROPERTIES_HANDLE properties, char* subject_value)
    int properties_get_reply_to(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE* reply_to_value)
    int properties_set_reply_to(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE reply_to_value)
    int properties_get_correlation_id(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE* correlation_id_value)
    int properties_set_correlation_id(PROPERTIES_HANDLE properties, c_amqpvalue.AMQP_VALUE correlation_id_value)
    int properties_get_content_type(PROPERTIES_HANDLE properties, char** content_type_value)
    int properties_set_content_type(PROPERTIES_HANDLE properties, char* content_type_value)
    int properties_get_content_encoding(PROPERTIES_HANDLE properties, char** content_encoding_value)
    int properties_set_content_encoding(PROPERTIES_HANDLE properties, char* content_encoding_value)
    int properties_get_absolute_expiry_time(PROPERTIES_HANDLE properties, c_amqpvalue.timestamp* absolute_expiry_time_value)
    int properties_set_absolute_expiry_time(PROPERTIES_HANDLE properties, c_amqpvalue.timestamp absolute_expiry_time_value)
    int properties_get_creation_time(PROPERTIES_HANDLE properties, c_amqpvalue.timestamp* creation_time_value)
    int properties_set_creation_time(PROPERTIES_HANDLE properties, c_amqpvalue.timestamp creation_time_value)
    int properties_get_group_id(PROPERTIES_HANDLE properties, char** group_id_value)
    int properties_set_group_id(PROPERTIES_HANDLE properties, char* group_id_value)
    int properties_get_group_sequence(PROPERTIES_HANDLE properties, sequence_no* group_sequence_value)
    int properties_set_group_sequence(PROPERTIES_HANDLE properties, sequence_no group_sequence_value)
    int properties_get_reply_to_group_id(PROPERTIES_HANDLE properties, char** reply_to_group_id_value)
    int properties_set_reply_to_group_id(PROPERTIES_HANDLE properties, char* reply_to_group_id_value)


    # source/target types
    ctypedef stdint.uint32_t terminus_durability
    cdef stdint.uint32_t terminus_durability_none
    cdef stdint.uint32_t terminus_durability_configuration
    cdef stdint.uint32_t terminus_durability_unsettled_state

    ctypedef const char* terminus_expiry_policy
    cdef const char* terminus_expiry_policy_link_detach
    cdef const char* terminus_expiry_policy_session_end
    cdef const char* terminus_expiry_policy_connection_close
    cdef const char* terminus_expiry_policy_never

    ctypedef fields node_properties
    ctypedef c_amqpvalue.AMQP_VALUE filter_set  # Map

    # source
    ctypedef struct SOURCE_HANDLE:
        pass

    SOURCE_HANDLE source_create()
    SOURCE_HANDLE source_clone(SOURCE_HANDLE value)
    void source_destroy(SOURCE_HANDLE source)
    bint is_source_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    int amqpvalue_get_source(c_amqpvalue.AMQP_VALUE value, SOURCE_HANDLE* SOURCE_handle)
    c_amqpvalue.AMQP_VALUE amqpvalue_create_source(SOURCE_HANDLE source)

    int source_get_address(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE* address_value)
    int source_set_address(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE address_value)
    int source_get_durable(SOURCE_HANDLE source, terminus_durability* durable_value)
    int source_set_durable(SOURCE_HANDLE source, terminus_durability durable_value)
    int source_get_expiry_policy(SOURCE_HANDLE source, terminus_expiry_policy* expiry_policy_value)
    int source_set_expiry_policy(SOURCE_HANDLE source, terminus_expiry_policy expiry_policy_value)
    int source_get_timeout(SOURCE_HANDLE source, seconds* timeout_value)
    int source_set_timeout(SOURCE_HANDLE source, seconds timeout_value)
    int source_get_dynamic(SOURCE_HANDLE source, bint* dynamic_value)
    int source_set_dynamic(SOURCE_HANDLE source, bint dynamic_value)
    int source_get_dynamic_node_properties(SOURCE_HANDLE source, node_properties* dynamic_node_properties_value)
    int source_set_dynamic_node_properties(SOURCE_HANDLE source, node_properties dynamic_node_properties_value)
    int source_get_distribution_mode(SOURCE_HANDLE source, const char** distribution_mode_value)
    int source_set_distribution_mode(SOURCE_HANDLE source, const char* distribution_mode_value)
    int source_get_filter(SOURCE_HANDLE source, filter_set* filter_value)
    int source_set_filter(SOURCE_HANDLE source, filter_set filter_value)
    #int source_get_default_outcome(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE* default_outcome_value)
    #int source_set_default_outcome(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE default_outcome_value)
    #int source_get_outcomes(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE* outcomes_value)
    #int source_set_outcomes(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE outcomes_value)
    #int source_get_capabilities(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE* capabilities_value)
    #int source_set_capabilities(SOURCE_HANDLE source, c_amqpvalue.AMQP_VALUE capabilities_value)

    # target
    ctypedef struct TARGET_HANDLE:
        pass

    TARGET_HANDLE target_create()
    TARGET_HANDLE target_clone(TARGET_HANDLE value)
    void target_destroy(TARGET_HANDLE target)
    bint is_target_type_by_descriptor(c_amqpvalue.AMQP_VALUE descriptor)
    int amqpvalue_get_target(c_amqpvalue.AMQP_VALUE value, TARGET_HANDLE* TARGET_handle)
    c_amqpvalue.AMQP_VALUE amqpvalue_create_target(TARGET_HANDLE target)

    int target_get_address(TARGET_HANDLE target, c_amqpvalue.AMQP_VALUE* address_value)
    int target_set_address(TARGET_HANDLE target, c_amqpvalue.AMQP_VALUE address_value)
    int target_get_durable(TARGET_HANDLE target, terminus_durability* durable_value)
    int target_set_durable(TARGET_HANDLE target, terminus_durability durable_value)
    int target_get_expiry_policy(TARGET_HANDLE target, terminus_expiry_policy* expiry_policy_value)
    int target_set_expiry_policy(TARGET_HANDLE target, terminus_expiry_policy expiry_policy_value)
    int target_get_timeout(TARGET_HANDLE target, seconds* timeout_value)
    int target_set_timeout(TARGET_HANDLE target, seconds timeout_value)
    int target_get_dynamic(TARGET_HANDLE target, bint* dynamic_value)
    int target_set_dynamic(TARGET_HANDLE target, bint dynamic_value)
    int target_get_dynamic_node_properties(TARGET_HANDLE target, node_properties* dynamic_node_properties_value)
    int target_set_dynamic_node_properties(TARGET_HANDLE target, node_properties dynamic_node_properties_value)
    #int target_get_capabilities(TARGET_HANDLE target, c_amqpvalue.AMQP_VALUE* capabilities_value)
    #int target_set_capabilities(TARGET_HANDLE target, c_amqpvalue.AMQP_VALUE capabilities_value)
