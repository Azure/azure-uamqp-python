#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_amqp_management
cimport c_message


_logger = logging.getLogger(__name__)


cpdef create_management_operation(cSession session, const char* management_node):
    mgr_op = cManagementOperation()
    mgr_op.create(session, management_node)
    return mgr_op


cdef class cManagementOperation(StructBase):

    cdef c_amqp_management.AMQP_MANAGEMENT_HANDLE _c_value
    cdef _session

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating cManagementOperation")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cManagementOperation")
            c_amqp_management.amqp_management_destroy(self._c_value)
            self._c_value = <c_amqp_management.AMQP_MANAGEMENT_HANDLE>NULL
            self._session = None

    cdef wrap(self, cManagementOperation value):
        self.destroy()
        self._session = value._session
        self._c_value = value._c_value
        self._validate()

    cdef create(self, cSession session, const char* management_node):
        self.destroy()
        self._session = session
        self._c_value = c_amqp_management.amqp_management_create(<c_session.SESSION_HANDLE>session._c_value, management_node)
        self._validate()

    cpdef set_trace(self, bint value):
        c_amqp_management.amqp_management_set_trace(self._c_value, value)

    cpdef set_response_field_names(self, const char* status_code, const char* status_description):
        if c_amqp_management.amqp_management_set_override_status_code_key_name(self._c_value, status_code) != 0:
            self._value_error("Failed to set status code field name.")
        if c_amqp_management.amqp_management_set_override_status_description_key_name(self._c_value, status_description) != 0:
            self._value_error("Failed to set status description field name.")

    cpdef open(self, callback_context):
        cdef void *context
        if callback_context is None:
            context = <void*>NULL
        else:
            context = <void*>callback_context
        if c_amqp_management.amqp_management_open_async(self._c_value, on_amqp_management_open_complete, context, on_amqp_management_error, context) != 0:
            self._value_error("Unable to open management link.")

    cpdef close(self):
        if c_amqp_management.amqp_management_close(self._c_value) != 0:
            self._value_error("Unable to close management link.")

    cpdef execute(self, const char* operation, const char* type, locales, cMessage message, callback_context):
        cdef const char* c_locales
        cdef void *context
        if locales is None:
            c_locales = <const char*>NULL
        else:
            c_locales = <const char*>locales
        if callback_context is None:
            context = <void*>NULL
        else:
            context = <void*>callback_context
        if <void*>c_amqp_management.amqp_management_execute_operation_async(self._c_value, operation, type, c_locales, message._c_value, on_execute_operation_complete, context) == NULL:
            self._value_error("Unable to execute management operation.")


#### Management Link Callbacks

cdef void on_amqp_management_open_complete(void* context, c_amqp_management.AMQP_MANAGEMENT_OPEN_RESULT_TAG open_result):
    _logger.debug("Management link open: %r", open_result)
    if context != NULL:
        context_obj = <object>context
        context_obj._management_open_complete(open_result)

cdef void on_amqp_management_error(void* context):
    _logger.debug("Management link error")
    if context != NULL:
        context_obj = <object>context
        context_obj._management_operation_error()

cdef void on_execute_operation_complete(void* context, c_amqp_management.AMQP_MANAGEMENT_EXECUTE_OPERATION_RESULT_TAG execute_operation_result, unsigned int status_code, const char* status_description, c_message.MESSAGE_HANDLE message):
    cdef c_message.MESSAGE_HANDLE cloned
    description = "None" if <void*>status_description == NULL else status_description
    _logger.debug("Management op complete: %r, status code: %r, description: %r", execute_operation_result, status_code, description)
    if context != NULL:
        context_obj = <object>context
        if status_code == 0:
            context_obj(execute_operation_result, status_code, description, None)
        else:
            if <void*>message != NULL:
                cloned = c_message.message_clone(message)
                wrapped_message = message_factory(cloned)
            else:
                wrapped_message = None
            context_obj(execute_operation_result, status_code, description, wrapped_message)
