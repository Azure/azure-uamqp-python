#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqp_definitions
cimport c_amqpvalue
cimport c_session
cimport c_async_operation

cdef extern from "azure_uamqp_c/link.h":

    ctypedef struct LINK_HANDLE:
        pass

    ctypedef struct ON_LINK_DETACH_EVENT_SUBSCRIPTION_HANDLE:
        pass

    cdef enum LINK_STATE_TAG:
        LINK_STATE_DETACHED,
        LINK_STATE_HALF_ATTACHED_ATTACH_SENT,
        LINK_STATE_HALF_ATTACHED_ATTACH_RECEIVED,
        LINK_STATE_ATTACHED,
        LINK_STATE_ERROR

    cdef enum LINK_TRANSFER_RESULT_TAG:
        LINK_TRANSFER_ERROR,
        LINK_TRANSFER_BUSY

    cdef enum LINK_DELIVERY_SETTLE_REASON_TAG:
        LINK_DELIVERY_SETTLE_REASON_DISPOSITION_RECEIVED,
        LINK_DELIVERY_SETTLE_REASON_SETTLED,
        LINK_DELIVERY_SETTLE_REASON_NOT_DELIVERED,
        LINK_DELIVERY_SETTLE_REASON_TIMEOUT,
        LINK_DELIVERY_SETTLE_REASON_CANCELLED

    ctypedef void (*ON_LINK_DETACH_RECEIVED)(void* context, c_amqp_definitions.ERROR_HANDLE error)

    LINK_HANDLE link_create(c_session.SESSION_HANDLE session, const char* name, c_amqp_definitions.role role, c_amqpvalue.AMQP_VALUE source, c_amqpvalue.AMQP_VALUE target)
    void link_destroy(LINK_HANDLE handle)
    void link_dowork(LINK_HANDLE link)
    int link_set_snd_settle_mode(LINK_HANDLE link, c_amqp_definitions.sender_settle_mode snd_settle_mode)
    int link_get_snd_settle_mode(LINK_HANDLE link, c_amqp_definitions.sender_settle_mode* snd_settle_mode)
    int link_set_rcv_settle_mode(LINK_HANDLE link, c_amqp_definitions.receiver_settle_mode rcv_settle_mode)
    int link_get_rcv_settle_mode(LINK_HANDLE link, c_amqp_definitions.receiver_settle_mode* rcv_settle_mode)
    int link_set_initial_delivery_count(LINK_HANDLE link, c_amqp_definitions.sequence_no initial_delivery_count)
    int link_get_initial_delivery_count(LINK_HANDLE link, c_amqp_definitions.sequence_no* initial_delivery_count)
    int link_set_max_link_credit(LINK_HANDLE link, stdint.uint32_t max_link_credit)
    int link_set_max_message_size(LINK_HANDLE link, stdint.uint64_t max_message_size)
    int link_get_max_message_size(LINK_HANDLE link, stdint.uint64_t* max_message_size)
    int link_get_peer_max_message_size(LINK_HANDLE link, stdint.uint64_t* peer_max_message_size)
    int link_set_attach_properties(LINK_HANDLE link, c_amqp_definitions.fields attach_properties)
    int link_set_desired_capabilities(LINK_HANDLE link, c_amqpvalue.AMQP_VALUE desired_capabilities)
    int link_get_desired_capabilities(LINK_HANDLE link, c_amqpvalue.AMQP_VALUE* desired_capabilities)
    int link_get_name(LINK_HANDLE link, const char** link_name)
    int link_get_received_message_id(LINK_HANDLE link, c_amqp_definitions.delivery_number* message_id)
    int link_reset_link_credit(LINK_HANDLE link, stdint.uint32_t link_credit, bint drain)

    ON_LINK_DETACH_EVENT_SUBSCRIPTION_HANDLE link_subscribe_on_link_detach_received(LINK_HANDLE link, ON_LINK_DETACH_RECEIVED on_link_detach_received, void* context)
    void link_unsubscribe_on_link_detach_received(ON_LINK_DETACH_EVENT_SUBSCRIPTION_HANDLE event_subscription)
