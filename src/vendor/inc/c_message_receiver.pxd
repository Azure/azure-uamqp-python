#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

cimport c_amqp_definitions
cimport c_message
cimport c_link
cimport c_amqpvalue

cdef extern from "azure_uamqp_c/message_receiver.h":

    cdef enum MESSAGE_RECEIVER_STATE_TAG:
        MESSAGE_RECEIVER_STATE_IDLE,
        MESSAGE_RECEIVER_STATE_OPENING,
        MESSAGE_RECEIVER_STATE_OPEN,
        MESSAGE_RECEIVER_STATE_CLOSING,
        MESSAGE_RECEIVER_STATE_ERROR

    ctypedef struct MESSAGE_RECEIVER_HANDLE:
        pass

    ctypedef c_amqpvalue.AMQP_VALUE (*ON_MESSAGE_RECEIVED)(const void* context, c_message.MESSAGE_HANDLE message)
    ctypedef void (*ON_MESSAGE_RECEIVER_STATE_CHANGED)(const void* context, MESSAGE_RECEIVER_STATE_TAG new_state, MESSAGE_RECEIVER_STATE_TAG previous_state)

    MESSAGE_RECEIVER_HANDLE messagereceiver_create(c_link.LINK_HANDLE link, ON_MESSAGE_RECEIVER_STATE_CHANGED on_message_receiver_state_changed, void* context)
    void messagereceiver_destroy(MESSAGE_RECEIVER_HANDLE message_receiver)
    int messagereceiver_open(MESSAGE_RECEIVER_HANDLE message_receiver, ON_MESSAGE_RECEIVED on_message_received, void* callback_context)
    int messagereceiver_close(MESSAGE_RECEIVER_HANDLE message_receiver)
    int messagereceiver_get_link_name(MESSAGE_RECEIVER_HANDLE message_receiver, const char** link_name)
    int messagereceiver_get_received_message_id(MESSAGE_RECEIVER_HANDLE message_receiver, c_amqp_definitions.delivery_number* message_number)
    int messagereceiver_send_message_disposition(MESSAGE_RECEIVER_HANDLE message_receiver, const char* link_name, c_amqp_definitions.delivery_number message_number, c_amqpvalue.AMQP_VALUE delivery_state)
    void messagereceiver_set_trace(MESSAGE_RECEIVER_HANDLE message_receiver, bint trace_on)
