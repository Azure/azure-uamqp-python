#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_xio
cimport c_sasl_mechanism


_logger = logging.getLogger(__name__)


cpdef _get_sasl_mechanism_interface():
    cdef const c_sasl_mechanism.SASL_MECHANISM_INTERFACE_DESCRIPTION* interface
    interface = c_sasl_mechanism.saslmssbcbs_get_interface()
    if <void*>interface == NULL:
        raise ValueError("Failed to create SASL CBS Interface description")
    desc = SASLMechanismInterfaceDescription()
    desc.wrap(interface)
    return desc


cpdef saslanonymous_get_interface():
    cdef c_sasl_mechanism.SASL_MECHANISM_INTERFACE_DESCRIPTION* io_desc
    io_desc = c_sasl_mechanism.saslanonymous_get_interface()
    if <void*>io_desc == NULL:
        raise ValueError("Failed to create SASL Anonymous Interface description")

    interface = SASLMechanismInterfaceDescription()
    interface.wrap(io_desc)
    return interface


cpdef saslplain_get_interface():
    cdef c_sasl_mechanism.SASL_MECHANISM_INTERFACE_DESCRIPTION* io_desc
    io_desc = c_sasl_mechanism.saslplain_get_interface()
    if <void*>io_desc == NULL:
        raise ValueError("Failed to create SASL plain Interface description")

    interface = SASLMechanismInterfaceDescription()
    interface.wrap(io_desc)
    return interface


cpdef get_sasl_mechanism(SASLMechanismInterfaceDescription interface=None):
    if interface is None:
        interface = _get_sasl_mechanism_interface()
    sasl_mechanism = SASLMechanism()
    sasl_mechanism.create(interface)
    return sasl_mechanism


cpdef get_plain_sasl_mechanism(SASLMechanismInterfaceDescription interface, SASLPlainConfig parameters):
    _logger.debug("Creating SASL Mechanism")
    sasl_mechanism = SASLMechanism()
    sasl_mechanism.create_with_parameters(interface, &parameters._c_value)
    return sasl_mechanism



cdef class SASLMechanism(StructBase):

    cdef c_sasl_mechanism.SASL_MECHANISM_HANDLE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating SASLMechanism")
        self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying SASLMechanism")
            c_sasl_mechanism.saslmechanism_destroy(self._c_value)
            self._c_value = <c_sasl_mechanism.SASL_MECHANISM_HANDLE>NULL

    cdef wrap(self, c_sasl_mechanism.SASL_MECHANISM_HANDLE value):
        self.destroy()
        self._c_value = value
        self._create()

    cdef create(self, SASLMechanismInterfaceDescription sasl_mechanism_interface_description):
        self.destroy()
        self._c_value = c_sasl_mechanism.saslmechanism_create(sasl_mechanism_interface_description._c_value, NULL)
        self._create()

    cdef create_with_parameters(self, SASLMechanismInterfaceDescription sasl_mechanism_interface_description, void *parameters):
        self.destroy()
        self._c_value = c_sasl_mechanism.saslmechanism_create(sasl_mechanism_interface_description._c_value, parameters)
        self._create()


cdef class SASLMechanismInterfaceDescription(object):

    cdef c_sasl_mechanism.SASL_MECHANISM_INTERFACE_DESCRIPTION* _c_value

    def __cinit__(self):
        pass

    cdef wrap(self, c_sasl_mechanism.SASL_MECHANISM_INTERFACE_DESCRIPTION* value):
        self._c_value = value


cdef class SASLClientIOConfig(object):

    cdef c_sasl_mechanism.SASLCLIENTIO_CONFIG _c_value
    cdef XIO _underlying_io

    def __cinit__(self, XIO underlying_io, SASLMechanism sasl_mechanism):
        if <void*>underlying_io._c_value is NULL:
            raise ValueError("UnderLying IO must not be NULL")
        if <void*>sasl_mechanism._c_value is NULL:
            raise ValueError("SASL Mechanism must not be NULL")

        self._underlying_io = underlying_io
        self._c_value = c_sasl_mechanism.SASLCLIENTIO_CONFIG(
            <c_xio.XIO_HANDLE>underlying_io._c_value,
            <c_sasl_mechanism.SASL_MECHANISM_HANDLE>sasl_mechanism._c_value
        )


cdef class SASLPlainConfig(object):

    cdef c_sasl_mechanism.SASL_PLAIN_CONFIG _c_value

    def __cinit__(self):
        self._c_value = c_sasl_mechanism.SASL_PLAIN_CONFIG(NULL, NULL, NULL)
        self._c_value.authcid = NULL
        self._c_value.passwd = NULL
        self._c_value.authzid = NULL

    @property
    def authcid(self):
        return self._c_value.authcid

    @authcid.setter
    def authcid(self, const char* value):
        self._c_value.authcid = value

    @property
    def passwd(self):
        return self._c_value.passwd

    @passwd.setter
    def passwd(self, const char* value):
        self._c_value.passwd = value

    @property
    def authzid(self):
        return self._c_value.authzid

    @authzid.setter
    def authzid(self, const char* value):
        self._c_value.authzid = value
