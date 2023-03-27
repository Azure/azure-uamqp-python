#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_strings


_logger = logging.getLogger(__name__)


cpdef create_empty_string():
    new_string = AMQPString()
    return new_string


cpdef create_string_from_value(value, encoding='UTF-8'):
    if isinstance(value, str):
        value = value.encode(encoding)
    new_string = AMQPString()
    new_string.construct(<const char*>value)
    return new_string


cdef class AMQPString(StructBase):

    cdef c_strings.STRING_HANDLE _c_value

    def __cinit__(self):
        self._c_value = c_strings.STRING_new()
        self._validate()

    def __dealloc__(self):
        _logger.debug("Deallocating AMQPString")
        self.destroy()

    def __bytes__(self):
        return c_strings.STRING_c_str(self._c_value)

    def __str__(self):
        as_bytes = c_strings.STRING_c_str(self._c_value)
        return str(as_bytes, encoding="UTF-8", errors="ignore" )

    def __unicode__(self):
        as_bytes = c_strings.STRING_c_str(self._c_value)
        try:
            return str(as_bytes.decode('UTF-8'))
        except UnicodeDecodeError:
            return str(as_bytes)

    def __eq__(self, AMQPString other):
        if c_strings.STRING_compare(self._c_value, other._c_value) == 0:
            return True
        return False

    def __ne__(self, AMQPString other):
        if c_strings.STRING_compare(self._c_value, other._c_value) == 0:
            return False
        return True

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                _logger.debug("Destroying AMQPString")
                c_strings.STRING_delete(self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
            self._c_value = <c_strings.STRING_HANDLE>NULL

    cdef wrap(self, c_strings.STRING_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    cdef construct(self, const char* value):
        self.destroy()
        self._c_value = c_strings.STRING_construct(value)
        self._validate()

    cpdef append(self, other):
        if isinstance(other, AMQPString):
            if c_strings.STRING_concat_with_STRING(self._c_value, <c_strings.STRING_HANDLE>other._c_value) != 0:
                self._value_error("Failed to append AMQPString value.")
        else:
            if c_strings.STRING_concat(self._c_value, <char*>other) != 0:
                self._value_error("Failed to append string.")

    cpdef clone(self):
        cdef c_strings.STRING_HANDLE value
        value = c_strings.STRING_clone(self._c_value)
        if <void*>value == NULL:
            self._null_error("Failed to clone AMQPString value.")
        cloned_value = AMQPString()
        cloned_value.wrap(value)
        return cloned_value
