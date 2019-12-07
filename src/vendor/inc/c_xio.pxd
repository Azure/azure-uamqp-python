#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_utils


cdef extern from "azure_c_shared_utility/xio.h":

    ctypedef void* CONCRETE_IO_HANDLE
    ctypedef void* XIO_HANDLE

    cdef enum IO_SEND_RESULT_TAG:
        IO_SEND_OK,
        IO_SEND_ERROR,
        IO_SEND_CANCELLED

    cdef enum IO_OPEN_RESULT_TAG:
        IO_OPEN_OK,
        IO_OPEN_ERROR,
        IO_OPEN_CANCELLED

    ctypedef void (*ON_BYTES_RECEIVED)(void* context, const unsigned char* buffer, size_t size)
    ctypedef void (*ON_SEND_COMPLETE)(void* context, IO_SEND_RESULT_TAG send_result)
    ctypedef void (*ON_IO_OPEN_COMPLETE)(void* context, IO_OPEN_RESULT_TAG open_result)
    ctypedef void (*ON_IO_CLOSE_COMPLETE)(void* context)
    ctypedef void (*ON_IO_ERROR)(void* context)

    ctypedef c_utils.OPTIONHANDLER_HANDLE (*IO_RETRIEVEOPTIONS)(CONCRETE_IO_HANDLE concrete_io)
    ctypedef CONCRETE_IO_HANDLE (*IO_CREATE)(void* io_create_parameters)
    ctypedef void (*IO_DESTROY)(CONCRETE_IO_HANDLE concrete_io)
    ctypedef int (*IO_OPEN)(CONCRETE_IO_HANDLE concrete_io, ON_IO_OPEN_COMPLETE on_io_open_complete, void* on_io_open_complete_context, ON_BYTES_RECEIVED on_bytes_received, void* on_bytes_received_context, ON_IO_ERROR on_io_error, void* on_io_error_context)
    ctypedef int (*IO_CLOSE)(CONCRETE_IO_HANDLE concrete_io, ON_IO_CLOSE_COMPLETE on_io_close_complete, void* callback_context)
    ctypedef int (*IO_SEND)(CONCRETE_IO_HANDLE concrete_io, const void* buffer, size_t size, ON_SEND_COMPLETE on_send_complete, void* callback_context)
    ctypedef void (*IO_DOWORK)(CONCRETE_IO_HANDLE concrete_io)
    ctypedef int (*IO_SETOPTION)(CONCRETE_IO_HANDLE concrete_io, const char* optionName, const void* value)

    ctypedef struct IO_INTERFACE_DESCRIPTION_TAG:
        IO_RETRIEVEOPTIONS concrete_io_retrieveoptions
        IO_CREATE concrete_io_create
        IO_DESTROY concrete_io_destroy
        IO_OPEN concrete_io_open
        IO_CLOSE concrete_io_close
        IO_SEND concrete_io_send
        IO_DOWORK concrete_io_dowork
        IO_SETOPTION concrete_io_setoption

    ctypedef IO_INTERFACE_DESCRIPTION_TAG IO_INTERFACE_DESCRIPTION

    XIO_HANDLE xio_create(const IO_INTERFACE_DESCRIPTION* io_interface_description, const void* io_create_parameters)
    void xio_destroy(XIO_HANDLE xio)
    int xio_open(XIO_HANDLE xio, ON_IO_OPEN_COMPLETE on_io_open_complete, void* on_io_open_complete_context, ON_BYTES_RECEIVED on_bytes_received, void* on_bytes_received_context, ON_IO_ERROR on_io_error, void* on_io_error_context)
    int xio_close(XIO_HANDLE xio, ON_IO_CLOSE_COMPLETE on_io_close_complete, void* callback_context)
    int xio_send(XIO_HANDLE xio, const void* buffer, size_t size, ON_SEND_COMPLETE on_send_complete, void* callback_context)
    void xio_dowork(XIO_HANDLE xio)
    int xio_setoption(XIO_HANDLE xio, const char* optionName, const void* value)
    c_utils.OPTIONHANDLER_HANDLE xio_retrieveoptions(XIO_HANDLE xio)
