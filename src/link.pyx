#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
from libc cimport stdint

cimport c_link
cimport c_session
cimport c_amqp_definitions
cimport c_amqpvalue


_logger = logging.getLogger(__name__)


cpdef create_link(cSession session, const char* name, bint role, AMQPValue source, AMQPValue target):
    new_link = cLink()
    new_link.create(session, name, <c_amqp_definitions.role>role, <c_amqpvalue.AMQP_VALUE>source._c_value, <c_amqpvalue.AMQP_VALUE>target._c_value)
    return new_link


cdef class cLink(StructBase):

    cdef c_link.LINK_HANDLE _c_value
    cdef c_link.ON_LINK_DETACH_EVENT_SUBSCRIPTION_HANDLE _detach_event
    cdef cSession _session

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating cLink")
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
            _logger.debug("Destroying cLink")
            c_link.link_destroy(self._c_value)
            self._c_value = <c_link.LINK_HANDLE>NULL
            self._session = None

    cdef wrap(self, cLink value):
        self.destroy()
        self._session = value._session
        self._c_value = value._c_value
        self._create()

    cdef create(self, cSession session, const char* name, c_amqp_definitions.role role, c_amqpvalue.AMQP_VALUE source, c_amqpvalue.AMQP_VALUE target):
        self.destroy()
        self._session = session
        self._c_value = c_link.link_create(<c_session.SESSION_HANDLE>session._c_value, name, role, source, target)
        self._create()

    cpdef subscribe_to_detach_event(self, on_detch_received):
        self._detach_event = c_link.link_subscribe_on_link_detach_received(
            self._c_value,
            <c_link.ON_LINK_DETACH_RECEIVED>on_link_detach_received,
            <void*>on_detch_received)
        if <void*>self._detach_event == NULL:
            self._value_error("Unable to register DETACH event handler.")

    cpdef unsubscribe_to_detach_event(self):
        c_link.link_unsubscribe_on_link_detach_received(self._detach_event)

    cpdef reset_link_credit(self, stdint.uint32_t link_credit, bint drain):
        _logger.debug("send flow, reset link credit to %r and drain to %r", link_credit, drain)
        if c_link.link_reset_link_credit(self._c_value, link_credit, drain) != 0:
            self._value_error("Unable to reset link credit and send flow.")

    @property
    def send_settle_mode(self):
        cdef c_amqp_definitions.sender_settle_mode snd_settle_mode
        if  c_link.link_get_snd_settle_mode(self._c_value, &snd_settle_mode) != 0:
            self._value_error()
        return <stdint.uint8_t>snd_settle_mode

    @send_settle_mode.setter
    def send_settle_mode(self, stdint.uint8_t value):
        if c_link.link_set_snd_settle_mode(self._c_value, <c_amqp_definitions.sender_settle_mode>value) != 0:
            self._value_error()

    @property
    def receive_settle_mode(self):
        cdef c_amqp_definitions.receiver_settle_mode rcv_settle_mode
        if  c_link.link_get_rcv_settle_mode(self._c_value, &rcv_settle_mode) != 0:
            self._value_error()
        return <stdint.uint8_t>rcv_settle_mode

    @receive_settle_mode.setter
    def receive_settle_mode(self, stdint.uint8_t value):
        if c_link.link_set_rcv_settle_mode(self._c_value, <c_amqp_definitions.receiver_settle_mode>value) != 0:
            self._value_error()

    @property
    def max_message_size(self):
        cdef stdint.uint64_t value
        if c_link.link_get_max_message_size(self._c_value, &value) != 0:
            self._value_error()
        return value

    @max_message_size.setter
    def max_message_size(self, stdint.uint64_t value):
        if c_link.link_set_max_message_size(self._c_value, value) != 0:
            self._value_error()

    @property
    def initial_delivery_count(self):
        cdef c_amqp_definitions.sequence_no value
        if c_link.link_get_initial_delivery_count(self._c_value, &value) != 0:
            self._value_error()
        return value

    @initial_delivery_count.setter
    def initial_delivery_count(self, c_amqp_definitions.sequence_no value):
        if c_link.link_set_initial_delivery_count(self._c_value, value) != 0:
            self._value_error()

    @property
    def peer_max_message_size(self):
        cdef stdint.uint64_t value
        if c_link.link_get_peer_max_message_size(self._c_value, &value) != 0:
            self._value_error()
        return value

    @property
    def name(self):
        cdef const char* value
        if c_link.link_get_name(self._c_value, &value) != 0:
            self._value_error()
        return value

    @property
    def desired_capabilities(self):
        cdef c_amqpvalue.AMQP_VALUE value
        if c_link.link_get_desired_capabilities(self._c_value, &value) != 0:
            self._value_error()
        return value_factory(value)

    cpdef do_work(self):
        c_link.link_dowork(self._c_value)

    cpdef set_prefetch_count(self, stdint.uint32_t prefetch):
        if c_link.link_set_max_link_credit(self._c_value, prefetch) != 0:
            self._value_error("Unable to set link credit.")

    cpdef set_attach_properties(self, AMQPValue properties):
        if c_link.link_set_attach_properties(self._c_value, <c_amqp_definitions.fields>properties._c_value) != 0:
            self._value_error("Unable to set link attach properties.")

    cpdef set_desired_capabilities(self, AMQPValue desired_capabilities):
        if c_link.link_set_desired_capabilities(self._c_value, <c_amqpvalue.AMQP_VALUE>desired_capabilities._c_value) != 0:
            self._value_error("Unable to set link desired capabilities.")


#### Callback

cdef void on_link_detach_received(void* context, c_amqp_definitions.ERROR_HANDLE error):
    cdef c_amqp_definitions.ERROR_HANDLE cloned
    context_obj = <object>context
    if <void*> error != NULL:
        cloned = c_amqp_definitions.error_clone(error)
        wrapped_error = error_factory(cloned)
    else:
        wrapped_error = None
    if hasattr(context_obj, '_detach_received'):
        context_obj._detach_received(wrapped_error)
