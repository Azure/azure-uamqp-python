#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_session
cimport c_strings
cimport c_async_operation


cdef enum AUTH_STATUS:
    AUTH_STATUS_OK,
    AUTH_STATUS_IDLE,
    AUTH_STATUS_IN_PROGRESS,
    AUTH_STATUS_TIMEOUT,
    AUTH_STATUS_REFRESH_REQUIRED,
    AUTH_STATUS_EXPIRED,
    AUTH_STATUS_ERROR,
    AUTH_STATUS_FAILURE


cdef extern from "azure_uamqp_c/cbs.h":

    cdef enum CBS_OPERATION_RESULT_TAG:
        CBS_OPERATION_RESULT_OK,
        CBS_OPERATION_RESULT_CBS_ERROR,
        CBS_OPERATION_RESULT_OPERATION_FAILED,
        CBS_OPERATION_RESULT_INSTANCE_CLOSED

    cdef enum CBS_OPEN_COMPLETE_RESULT_TAG:
        CBS_OPEN_OK,
        CBS_OPEN_ERROR,
        CBS_OPEN_CANCELLED

    ctypedef struct CBS_HANDLE:
        pass

    ctypedef void (*ON_CBS_OPEN_COMPLETE)(void* context, CBS_OPEN_COMPLETE_RESULT_TAG open_complete_result)
    ctypedef void (*ON_CBS_ERROR)(void* context)
    ctypedef void (*ON_CBS_OPERATION_COMPLETE)(void* context, CBS_OPERATION_RESULT_TAG complete_result, unsigned int status_code, const char* status_description)

    CBS_HANDLE cbs_create(c_session.SESSION_HANDLE session)
    void cbs_destroy(CBS_HANDLE cbs)
    int cbs_open_async(CBS_HANDLE cbs, ON_CBS_OPEN_COMPLETE on_cbs_open_complete, void* on_cbs_open_complete_context, ON_CBS_ERROR on_cbs_error, void* on_cbs_error_context)
    int cbs_close(CBS_HANDLE cbs)
    c_async_operation.ASYNC_OPERATION_HANDLE cbs_put_token_async(CBS_HANDLE cbs, const char* type, const char* audience, const char* token, ON_CBS_OPERATION_COMPLETE on_cbs_put_token_complete, void* on_cbs_put_token_complete_context)
    int cbs_delete_token_async(CBS_HANDLE cbs, const char* type, const char* audience, ON_CBS_OPERATION_COMPLETE on_cbs_delete_token_complete, void* on_cbs_delete_token_complete_context)
    int cbs_set_trace(CBS_HANDLE cbs, bint trace_on)
