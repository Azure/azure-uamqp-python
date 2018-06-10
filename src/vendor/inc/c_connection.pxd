#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqp_definitions
cimport c_amqpvalue
cimport c_xio

cdef extern from "azure_uamqp_c/connection.h":

    ctypedef struct CONNECTION_HANDLE:
        pass
    ctypedef struct ENDPOINT_HANDLE:
        pass
    ctypedef struct ON_CONNECTION_CLOSED_EVENT_SUBSCRIPTION_HANDLE:
        pass

    cdef enum CONNECTION_STATE_TAG:
        CONNECTION_STATE_START,
        CONNECTION_STATE_HDR_RCVD,
        CONNECTION_STATE_HDR_SENT,
        CONNECTION_STATE_HDR_EXCH,
        CONNECTION_STATE_OPEN_PIPE,
        CONNECTION_STATE_OC_PIPE,
        CONNECTION_STATE_OPEN_RCVD,
        CONNECTION_STATE_OPEN_SENT,
        CONNECTION_STATE_CLOSE_PIPE,
        CONNECTION_STATE_OPENED,
        CONNECTION_STATE_CLOSE_RCVD,
        CONNECTION_STATE_CLOSE_SENT,
        CONNECTION_STATE_DISCARDING,
        CONNECTION_STATE_END,
        CONNECTION_STATE_ERROR

    ctypedef CONNECTION_STATE_TAG CONNECTION_STATE

    ctypedef void (*ON_CONNECTION_STATE_CHANGED)(void* context, CONNECTION_STATE new_connection_state, CONNECTION_STATE previous_connection_state)
    ctypedef bint (*ON_NEW_ENDPOINT)(void* context, ENDPOINT_HANDLE new_endpoint)
    ctypedef void (*ON_CONNECTION_CLOSE_RECEIVED)(void* context, c_amqp_definitions.ERROR_HANDLE error)

    CONNECTION_HANDLE connection_create(c_xio.XIO_HANDLE io, const char* hostname, const char* container_id, ON_NEW_ENDPOINT on_new_endpoint, void* callback_context)
    CONNECTION_HANDLE connection_create2(c_xio.XIO_HANDLE xio, const char* hostname, const char* container_id, ON_NEW_ENDPOINT on_new_endpoint, void* callback_context, ON_CONNECTION_STATE_CHANGED on_connection_state_changed, void* on_connection_state_changed_context, c_xio.ON_IO_ERROR on_io_error, void* on_io_error_context)
    void connection_destroy(CONNECTION_HANDLE connection)
    int connection_open(CONNECTION_HANDLE connection)
    int connection_listen(CONNECTION_HANDLE connection)
    int connection_close(CONNECTION_HANDLE connection, const char* condition_value, const char* description, c_amqpvalue.AMQP_VALUE info)
    int connection_set_max_frame_size(CONNECTION_HANDLE connection, stdint.uint32_t max_frame_size)
    int connection_get_max_frame_size(CONNECTION_HANDLE connection, stdint.uint32_t* max_frame_size)
    int connection_set_channel_max(CONNECTION_HANDLE connection, stdint.uint16_t channel_max)
    int connection_get_channel_max(CONNECTION_HANDLE connection, stdint.uint16_t* channel_max)
    int connection_set_idle_timeout(CONNECTION_HANDLE connection, c_amqp_definitions.milliseconds idle_timeout)
    int connection_get_idle_timeout(CONNECTION_HANDLE connection, c_amqp_definitions.milliseconds* idle_timeout)
    int connection_set_properties(CONNECTION_HANDLE connection, c_amqp_definitions.fields properties)
    int connection_get_properties(CONNECTION_HANDLE connection, c_amqp_definitions.fields* properties)
    int connection_get_remote_max_frame_size(CONNECTION_HANDLE connection, stdint.uint32_t* remote_max_frame_size)
    int connection_set_remote_idle_timeout_empty_frame_send_ratio(CONNECTION_HANDLE connection, double idle_timeout_empty_frame_send_ratio)
    stdint.uint64_t connection_handle_deadlines(CONNECTION_HANDLE connection)
    void connection_dowork(CONNECTION_HANDLE connection) nogil
    void connection_set_trace(CONNECTION_HANDLE connection, bint trace_on)

    ON_CONNECTION_CLOSED_EVENT_SUBSCRIPTION_HANDLE connection_subscribe_on_connection_close_received(CONNECTION_HANDLE connection, ON_CONNECTION_CLOSE_RECEIVED on_connection_close_received, void* context)
    void connection_unsubscribe_on_connection_close_received(ON_CONNECTION_CLOSED_EVENT_SUBSCRIPTION_HANDLE event_subscription)

