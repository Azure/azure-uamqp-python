#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
from libc cimport stdint
cimport c_amqpvalue
cimport c_amqp_definitions
cimport c_session
cimport c_connection


_logger = logging.getLogger(__name__)


cpdef create_session(Connection connection, on_link_attached_context):
    session = cSession()
    session.create(connection, <c_session.ON_LINK_ATTACHED>on_link_attached, <void*>on_link_attached_context)
    return session


cdef class cSession(StructBase):

    _links = []
    cdef c_session.SESSION_HANDLE _c_value
    cdef Connection _connection

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating cSession")
        self.destroy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.destroy()

    @property
    def incoming_window(self):
        cdef stdint.uint32_t value
        if c_session.session_get_incoming_window(self._c_value, &value) != 0:
            self._value_error()
        return value

    @incoming_window.setter
    def incoming_window(self, stdint.uint32_t value):
        if c_session.session_set_incoming_window(self._c_value, value) != 0:
            self._value_error()

    @property
    def outgoing_window(self):
        cdef stdint.uint32_t value
        if c_session.session_get_outgoing_window(self._c_value, &value) != 0:
            self._value_error()
        return value

    @outgoing_window.setter
    def outgoing_window(self, stdint.uint32_t value):
        if c_session.session_set_outgoing_window(self._c_value, value) != 0:
            self._value_error()

    @property
    def handle_max(self):
        cdef c_amqp_definitions.handle value
        if c_session.session_get_handle_max(self._c_value, &value) != 0:
            self._value_error()
        return value

    @handle_max.setter
    def handle_max(self, c_amqp_definitions.handle value):
        if c_session.session_set_handle_max(self._c_value, value) != 0:
            self._value_error()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cSession")
            c_session.session_destroy(self._c_value)
            self._c_value = <c_session.SESSION_HANDLE>NULL
            self._connection = None

    cdef wrap(self, cSession value):
        self.destroy()
        self._connection = value._connection
        self._c_value = value._c_value
        self._create()

    cdef create(self, Connection connection, c_session.ON_LINK_ATTACHED on_link_attached, void* callback_context):
        self.destroy()
        self._connection = connection
        self._c_value = c_session.session_create(connection._c_value, on_link_attached, callback_context)
        self._create()

    cpdef begin(self):
        if c_session.session_begin(self._c_value) != 0:
            self._value_error()

    cpdef end(self, const char* condition_value, const char* description):
        if c_session.session_end(self._c_value, condition_value, description) != 0:
            self._value_error()


#### Callback

cdef bint on_link_attached(
        void* context, c_session.LINK_ENDPOINT_HANDLE new_link_endpoint, const char* name,
        c_amqp_definitions.role role, c_amqpvalue.AMQP_VALUE source, c_amqpvalue.AMQP_VALUE target,
        c_amqp_definitions.fields properties):

    cdef c_amqp_definitions.SOURCE_HANDLE wrapped_source
    cdef c_amqp_definitions.TARGET_HANDLE wrapped_target
    cdef c_amqpvalue.AMQP_VALUE wrapped_props
    cdef c_amqpvalue.AMQP_VALUE cloned_source
    cdef c_amqpvalue.AMQP_VALUE cloned_target
    cdef stdint.uint32_t _value
    attach_properties = None

    context_obj = <object>context
    if <void*>context_obj == NULL:
        return True
    if <void*>properties != NULL:
        wrapped_props = c_amqpvalue.amqpvalue_clone(properties)
        attach_properties = value_factory(wrapped_props)

    if <void*>source == NULL or <void*>target == NULL:
        _logger.info("Link ATTACH frame missing source and/or target. DETACH pending.")
        context_obj._attach_received(None, None, attach_properties, "ATTACH frame Source and/or Target is NULL")
    else:
        try:
            cloned_source = c_amqpvalue.amqpvalue_clone(source)
            cloned_target = c_amqpvalue.amqpvalue_clone(target)
            if c_amqp_definitions.amqpvalue_get_source(cloned_source, &wrapped_source) != 0:
                context_obj._attach_received(None, None, attach_properties, "Unable to decode ATTACH frame source")
            elif c_amqp_definitions.amqpvalue_get_target(cloned_target, &wrapped_target) != 0:
                context_obj._attach_received(None, None, attach_properties, "Unable to decode ATTACH frame target")
            else:
                context_obj._attach_received(source_factory(wrapped_source), target_factory(wrapped_target), attach_properties, None)
        except Exception as e:
            _logger.info("Failed to process link ATTACH frame: %r", e)
        finally:
            c_amqpvalue.amqpvalue_destroy(cloned_source)
            c_amqpvalue.amqpvalue_destroy(cloned_target)
    return True
