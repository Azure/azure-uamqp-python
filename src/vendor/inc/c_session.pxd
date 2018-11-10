#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqpvalue
cimport c_connection
cimport c_amqp_definitions


cdef extern from "azure_uamqp_c/session.h":

    ctypedef struct SESSION_HANDLE:
        pass
    ctypedef struct LINK_ENDPOINT_HANDLE:
        pass

    ctypedef bint (*ON_LINK_ATTACHED)(void* context, LINK_ENDPOINT_HANDLE new_link_endpoint, const char* name, c_amqp_definitions.role role, c_amqpvalue.AMQP_VALUE source, c_amqpvalue.AMQP_VALUE target, c_amqp_definitions.fields properties)

    SESSION_HANDLE session_create(c_connection.CONNECTION_HANDLE connection, ON_LINK_ATTACHED on_link_attached, void* callback_context)
    int session_set_incoming_window(SESSION_HANDLE session, stdint.uint32_t incoming_window)
    int session_get_incoming_window(SESSION_HANDLE session, stdint.uint32_t* incoming_window)
    int session_set_outgoing_window(SESSION_HANDLE session, stdint.uint32_t outgoing_window)
    int session_get_outgoing_window(SESSION_HANDLE session, stdint.uint32_t* outgoing_window)
    int session_set_handle_max(SESSION_HANDLE session, c_amqp_definitions.handle handle_max)
    int session_get_handle_max(SESSION_HANDLE session, c_amqp_definitions.handle* handle_max)
    void session_destroy(SESSION_HANDLE session)
    int session_begin(SESSION_HANDLE session)
    int session_end(SESSION_HANDLE session, const char* condition_value, const char* description)
