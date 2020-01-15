#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging
from enum import Enum

# C imports
from libc cimport stdint
cimport c_amqp_definitions
cimport c_connection
cimport c_xio


_logger = logging.getLogger(__name__)


cpdef create_connection(XIO sasl_client, const char* hostname, const char* container_id, callback_context):
    conn = Connection()
    conn.create(sasl_client, hostname, container_id, on_connection_state_changed, on_io_error, <void*>callback_context)
    return conn


class ConnectionState(Enum):
    START = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_START
    HDR_RCVD = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_HDR_RCVD
    HDR_SENT = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_HDR_SENT
    HDR_EXCH = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_HDR_EXCH
    OPEN_PIPE = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_OPEN_PIPE
    OC_PIPE = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_OC_PIPE
    OPEN_RCVD = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_OPEN_RCVD
    OPEN_SENT = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_OPEN_SENT
    CLOSE_PIPE = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_CLOSE_PIPE
    OPENED = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_OPENED
    CLOSE_RCVD = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_CLOSE_RCVD
    CLOSE_SENT = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_CLOSE_SENT
    DISCARDING = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_DISCARDING
    END = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_END
    ERROR = c_connection.CONNECTION_STATE_TAG.CONNECTION_STATE_ERROR
    UNKNOWN = 999


cdef class Connection(StructBase):

    cdef c_connection.CONNECTION_HANDLE _c_value
    cdef c_connection.ON_CONNECTION_CLOSED_EVENT_SUBSCRIPTION_HANDLE _close_event
    cdef XIO _sasl_client

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating Connection")
        self.destroy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.destroy()

    cdef _create(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying Connection")
            c_connection.connection_destroy(self._c_value)
            self._c_value = <c_connection.CONNECTION_HANDLE>NULL
            self._sasl_client = None

    cdef wrap(self, Connection value):
        self.destroy()
        self._sasl_client = value._sasl_client
        self._c_value = value._c_value
        self._create()

    cdef create(self, XIO sasl_client, const char* hostname, const char* container_id, c_connection.ON_CONNECTION_STATE_CHANGED on_connection_state_changed, c_xio.ON_IO_ERROR on_io_error, void* callback_context):
        self.destroy()
        self._sasl_client = sasl_client
        self._c_value = c_connection.connection_create2(sasl_client._c_value, hostname, container_id, NULL, NULL, on_connection_state_changed, callback_context, on_io_error, callback_context)
        self._create()

    cpdef open(self):
        if c_connection.connection_open(self._c_value) != 0:
            self._value_error()

    cpdef close(self, const char* condition_value, const char* description):
        if c_connection.connection_close(self._c_value, condition_value, description, <c_amqpvalue.AMQP_VALUE>NULL) != 0:
            self._value_error()

    cpdef set_trace(self, bint value):
        c_connection.connection_set_trace(self._c_value, value)

    cpdef do_work(self):
        c_connection.connection_dowork(self._c_value)

    cpdef subscribe_to_close_event(self, on_close_received):
        self._close_event = c_connection.connection_subscribe_on_connection_close_received(
            self._c_value,
            <c_connection.ON_CONNECTION_CLOSE_RECEIVED>on_connection_close_received,
            <void*>on_close_received)
        if <void*>self._close_event == NULL:
            self._value_error("Unable to register CLOSE event handler.")

    cpdef unsubscribe_to_close_event(self):
        c_connection.connection_unsubscribe_on_connection_close_received(self._close_event)

    @property
    def max_frame_size(self):
        cdef stdint.uint32_t _value
        if c_connection.connection_get_max_frame_size(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            self._value_error()

    @max_frame_size.setter
    def max_frame_size(self, stdint.uint32_t value):
        if c_connection.connection_set_max_frame_size(self._c_value, value) != 0:
            self._value_error()

    @property
    def channel_max(self):
        cdef stdint.uint16_t _value
        if c_connection.connection_get_channel_max(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            self._value_error()

    @channel_max.setter
    def channel_max(self, stdint.uint16_t value):
        if c_connection.connection_set_channel_max(self._c_value, value) != 0:
            self._value_error()

    @property
    def idle_timeout(self):
        cdef c_amqp_definitions.milliseconds _value
        if c_connection.connection_get_idle_timeout(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            self._value_error()

    @idle_timeout.setter
    def idle_timeout(self, c_amqp_definitions.milliseconds value):
        if c_connection.connection_set_idle_timeout(self._c_value, value) != 0:
            self._value_error()

    @property
    def properties(self):
        cdef c_amqp_definitions.fields _value
        if c_connection.connection_get_properties(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return value_factory(_value)
        else:
            self._value_error()

    @properties.setter
    def properties(self, AMQPValue value):
        if c_connection.connection_set_properties(self._c_value, <c_amqp_definitions.fields>value._c_value) != 0:
            self._value_error()

    @property
    def remote_max_frame_size(self):
        cdef stdint.uint32_t _value
        if c_connection.connection_get_remote_max_frame_size(self._c_value, &_value) == 0:
            if <void*>_value == NULL:
                return None
            return _value
        else:
            self._value_error()


#### Callback

cdef void on_connection_state_changed(void* context, c_connection.CONNECTION_STATE_TAG new_connection_state, c_connection.CONNECTION_STATE_TAG previous_connection_state):
    if <void*>context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call on_connection_state_changed during garbage collection")
            return
        context_obj = <object>context
        try:
            context_obj._state_changed(previous_connection_state, new_connection_state)
        except AttributeError:
            _logger.info("Unknown connection state changed: %r to %r", previous_connection_state, new_connection_state)


cdef void on_io_error(void* context):
    if <void*>context != NULL:
        context_obj = <object>context
        if hasattr(context_obj, '_io_error'):
            context_obj._io_error()


cdef void on_connection_close_received(void* context, c_amqp_definitions.ERROR_HANDLE error):
    cdef c_amqp_definitions.ERROR_HANDLE cloned
    context_obj = <object>context
    if <void*> error != NULL:
        cloned = c_amqp_definitions.error_clone(error)
        wrapped_error = error_factory(cloned)
    else:
        wrapped_error = None
    if hasattr(context_obj, '_close_received'):
        context_obj._close_received(wrapped_error)
