#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_message
cimport c_link
cimport c_async_operation
cimport c_amqp_definitions
cimport c_amqpvalue


cdef extern from "azure_uamqp_c/message_sender.h":

    cdef enum MESSAGE_SEND_RESULT_TAG:
        MESSAGE_SEND_OK,
        MESSAGE_SEND_ERROR,
        MESSAGE_SEND_TIMEOUT,
        MESSAGE_SEND_CANCELLED

    cdef enum MESSAGE_SENDER_STATE_TAG:
        MESSAGE_SENDER_STATE_IDLE,
        MESSAGE_SENDER_STATE_OPENING,
        MESSAGE_SENDER_STATE_OPEN,
        MESSAGE_SENDER_STATE_CLOSING,
        MESSAGE_SENDER_STATE_ERROR

    ctypedef struct MESSAGE_SENDER_HANDLE:
        pass

    ctypedef void (*ON_MESSAGE_SEND_COMPLETE)(void* context, MESSAGE_SEND_RESULT_TAG send_result, c_amqpvalue.AMQP_VALUE delivery_state)
    ctypedef void (*ON_MESSAGE_SENDER_STATE_CHANGED)(void* context, MESSAGE_SENDER_STATE_TAG new_state, MESSAGE_SENDER_STATE_TAG previous_state)

    MESSAGE_SENDER_HANDLE messagesender_create(c_link.LINK_HANDLE link, ON_MESSAGE_SENDER_STATE_CHANGED on_message_sender_state_changed, void* context)
    void messagesender_destroy(MESSAGE_SENDER_HANDLE message_sender)
    int messagesender_open(MESSAGE_SENDER_HANDLE message_sender)
    int messagesender_close(MESSAGE_SENDER_HANDLE message_sender)
    c_async_operation.ASYNC_OPERATION_HANDLE messagesender_send_async(MESSAGE_SENDER_HANDLE message_sender, c_message.MESSAGE_HANDLE message, ON_MESSAGE_SEND_COMPLETE on_message_send_complete, void* callback_context, c_amqp_definitions.tickcounter_ms_t timeout)
    void messagesender_set_trace(MESSAGE_SENDER_HANDLE message_sender, bint traceOn)
