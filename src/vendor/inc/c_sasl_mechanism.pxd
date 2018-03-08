#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint

cimport c_xio


cdef extern from "azure_uamqp_c/sasl_mechanism.h":

    ctypedef struct SASL_MECHANISM_HANDLE:
        pass

    ctypedef void* CONCRETE_SASL_MECHANISM_HANDLE

    ctypedef struct SASL_MECHANISM_BYTES_TAG:
        const void* bytes
        stdint.uint32_t length

    ctypedef SASL_MECHANISM_BYTES_TAG SASL_MECHANISM_BYTES

    ctypedef CONCRETE_SASL_MECHANISM_HANDLE (*SASL_MECHANISM_CREATE)(void* config)
    ctypedef void (*SASL_MECHANISM_DESTROY)(CONCRETE_SASL_MECHANISM_HANDLE concrete_sasl_mechanism)
    ctypedef int (*SASL_MECHANISM_GET_INIT_BYTES)(CONCRETE_SASL_MECHANISM_HANDLE concrete_sasl_mechanism, SASL_MECHANISM_BYTES* init_bytes)
    ctypedef const char* (*SASL_MECHANISM_GET_MECHANISM_NAME)(CONCRETE_SASL_MECHANISM_HANDLE concrete_sasl_mechanism)
    ctypedef int (*SASL_MECHANISM_CHALLENGE)(CONCRETE_SASL_MECHANISM_HANDLE concrete_sasl_mechanism, const SASL_MECHANISM_BYTES* challenge_bytes, SASL_MECHANISM_BYTES* response_bytes)

    ctypedef struct SASL_MECHANISM_INTERFACE_TAG:
        SASL_MECHANISM_CREATE concrete_sasl_mechanism_create
        SASL_MECHANISM_DESTROY concrete_sasl_mechanism_destroy
        SASL_MECHANISM_GET_INIT_BYTES concrete_sasl_mechanism_get_init_bytes
        SASL_MECHANISM_GET_MECHANISM_NAME concrete_sasl_mechanism_get_mechanism_name
        SASL_MECHANISM_CHALLENGE concrete_sasl_mechanism_challenge

    ctypedef SASL_MECHANISM_INTERFACE_TAG SASL_MECHANISM_INTERFACE_DESCRIPTION

    SASL_MECHANISM_HANDLE saslmechanism_create(const SASL_MECHANISM_INTERFACE_DESCRIPTION* sasl_mechanism_interface_description, void* sasl_mechanism_create_parameters)
    void saslmechanism_destroy(SASL_MECHANISM_HANDLE sasl_mechanism)
    int saslmechanism_get_init_bytes(SASL_MECHANISM_HANDLE sasl_mechanism, SASL_MECHANISM_BYTES* init_bytes)
    const char* saslmechanism_get_mechanism_name(SASL_MECHANISM_HANDLE sasl_mechanism)
    int saslmechanism_challenge(SASL_MECHANISM_HANDLE sasl_mechanism, const SASL_MECHANISM_BYTES* challenge_bytes, SASL_MECHANISM_BYTES* response_bytes)


cdef extern from "azure_uamqp_c/sasl_anonymous.h":

        const SASL_MECHANISM_INTERFACE_DESCRIPTION* saslanonymous_get_interface()


cdef extern from "azure_uamqp_c/sasl_plain.h":

    ctypedef struct SASL_PLAIN_CONFIG_TAG:
        const char* authcid
        const char* passwd
        const char* authzid

    ctypedef SASL_PLAIN_CONFIG_TAG SASL_PLAIN_CONFIG

    const SASL_MECHANISM_INTERFACE_DESCRIPTION* saslplain_get_interface()


cdef extern from "azure_uamqp_c/sasl_mssbcbs.h":

    CONCRETE_SASL_MECHANISM_HANDLE saslmssbcbs_create(void* config)
    void saslmssbcbs_destroy(CONCRETE_SASL_MECHANISM_HANDLE sasl_mechanism_concrete_handle)
    int saslmssbcbs_get_init_bytes(CONCRETE_SASL_MECHANISM_HANDLE sasl_mechanism_concrete_handle, SASL_MECHANISM_BYTES* init_bytes)
    const char* saslmssbcbs_get_mechanism_name(CONCRETE_SASL_MECHANISM_HANDLE sasl_mechanism)
    int saslmssbcbs_challenge(CONCRETE_SASL_MECHANISM_HANDLE concrete_sasl_mechanism, const SASL_MECHANISM_BYTES* challenge_bytes, SASL_MECHANISM_BYTES* response_bytes)
    const SASL_MECHANISM_INTERFACE_DESCRIPTION* saslmssbcbs_get_interface()


cdef extern from "azure_uamqp_c/saslclientio.h":

    ctypedef struct SASLCLIENTIO_CONFIG_TAG:
        c_xio.XIO_HANDLE underlying_io
        SASL_MECHANISM_HANDLE sasl_mechanism

    ctypedef SASLCLIENTIO_CONFIG_TAG SASLCLIENTIO_CONFIG

    const c_xio.IO_INTERFACE_DESCRIPTION* saslclientio_get_interface_description()
