#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_amqpvalue
cimport c_session
cimport c_message
cimport c_async_operation


cdef extern from "azure_uamqp_c/amqp_management.h":

    cdef enum AMQP_MANAGEMENT_EXECUTE_OPERATION_RESULT_TAG:
        AMQP_MANAGEMENT_EXECUTE_OPERATION_OK,
        AMQP_MANAGEMENT_EXECUTE_OPERATION_ERROR,
        AMQP_MANAGEMENT_EXECUTE_OPERATION_FAILED_BAD_STATUS,
        AMQP_MANAGEMENT_EXECUTE_OPERATION_INSTANCE_CLOSED

    cdef enum AMQP_MANAGEMENT_OPEN_RESULT_TAG:
        AMQP_MANAGEMENT_OPEN_OK,
        AMQP_MANAGEMENT_OPEN_ERROR,
        AMQP_MANAGEMENT_OPEN_CANCELLED

    ctypedef struct AMQP_MANAGEMENT_HANDLE:
        pass

    ctypedef void(*ON_AMQP_MANAGEMENT_OPEN_COMPLETE)(void* context, AMQP_MANAGEMENT_OPEN_RESULT_TAG open_result)
    ctypedef void(*ON_AMQP_MANAGEMENT_ERROR)(void* context)
    ctypedef void(*ON_AMQP_MANAGEMENT_EXECUTE_OPERATION_COMPLETE)(void* context, AMQP_MANAGEMENT_EXECUTE_OPERATION_RESULT_TAG execute_operation_result, unsigned int status_code, const char* status_description, c_message.MESSAGE_HANDLE message_handle);

    AMQP_MANAGEMENT_HANDLE amqp_management_create(c_session.SESSION_HANDLE session, const char* management_node)
    void amqp_management_destroy(AMQP_MANAGEMENT_HANDLE amqp_management)
    int amqp_management_open_async(AMQP_MANAGEMENT_HANDLE amqp_management, ON_AMQP_MANAGEMENT_OPEN_COMPLETE on_amqp_management_open_complete, void* on_amqp_management_open_complete_context, ON_AMQP_MANAGEMENT_ERROR on_amqp_management_error, void* on_amqp_management_error_context)
    int amqp_management_close(AMQP_MANAGEMENT_HANDLE amqp_management)
    c_async_operation.ASYNC_OPERATION_HANDLE amqp_management_execute_operation_async(AMQP_MANAGEMENT_HANDLE amqp_management, const char* operation, const char* type, const char* locales, c_message.MESSAGE_HANDLE message, ON_AMQP_MANAGEMENT_EXECUTE_OPERATION_COMPLETE on_execute_operation_complete, void* context)
    void amqp_management_set_trace(AMQP_MANAGEMENT_HANDLE amqp_management, bint trace_on)
    int amqp_management_set_override_status_code_key_name(AMQP_MANAGEMENT_HANDLE amqp_management, const char* override_status_code_key_name);
    int amqp_management_set_override_status_description_key_name(AMQP_MANAGEMENT_HANDLE amqp_management, const char* override_status_description_key_name);
