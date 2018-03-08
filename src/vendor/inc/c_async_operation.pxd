#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------


cdef extern from "azure_uamqp_c/async_operation.h":

    ctypedef struct ASYNC_OPERATION_HANDLE:
        pass

    ctypedef void (*ASYNC_OPERATION_CANCEL_HANDLER_FUNC)(ASYNC_OPERATION_HANDLE async_operation)

    ASYNC_OPERATION_HANDLE async_operation_create(ASYNC_OPERATION_CANCEL_HANDLER_FUNC async_operation_cancel_handler, size_t context_size)
    void async_operation_destroy(ASYNC_OPERATION_HANDLE async_operation)
    int async_operation_cancel(ASYNC_OPERATION_HANDLE async_operation)
