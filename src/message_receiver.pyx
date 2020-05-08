#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging

# C imports
cimport c_message_receiver
cimport c_message
cimport c_link
cimport c_amqpvalue



_logger = logging.getLogger(__name__)


cpdef create_message_receiver(cLink link, callback_context):
    receiver = cMessageReceiver()
    receiver.create(link, on_message_receiver_state_changed, <void*>callback_context)
    return receiver


cdef class cMessageReceiver(StructBase):

    cdef c_message_receiver.MESSAGE_RECEIVER_HANDLE _c_value
    cdef const char* _link_name
    cdef cLink _link

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating cMessageReceiver")
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cdef create(self, cLink link, c_message_receiver.ON_MESSAGE_RECEIVER_STATE_CHANGED on_message_sender_state_changed, void* context):
        self.destroy()
        self._link = link
        self._c_value = c_message_receiver.messagereceiver_create(<c_link.LINK_HANDLE>link._c_value, on_message_sender_state_changed, context)
        self._validate()
        if c_message_receiver.messagereceiver_get_link_name(self._c_value, &self._link_name)!= 0:
            self._value_error("Unable to retrieve message receiver link name.")

    cpdef open(self, callback_context):
        if c_message_receiver.messagereceiver_open(self._c_value, <c_message_receiver.ON_MESSAGE_RECEIVED>on_message_received, <void*>callback_context) != 0:
            self._value_error()

    cpdef close(self):
        if c_message_receiver.messagereceiver_close(self._c_value) != 0:
            self._value_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying cMessageReceiver")
            c_message_receiver.messagereceiver_destroy(self._c_value)
            self._c_value = <c_message_receiver.MESSAGE_RECEIVER_HANDLE>NULL
            self._link = None

    cpdef last_received_message_number(self):
        cdef c_amqp_definitions.delivery_number message_number
        if c_message_receiver.messagereceiver_get_received_message_id(self._c_value, &message_number) != 0:
            self._value_error("Unable to retrieve last received message number.")
        return message_number

    cpdef settle_accepted_message(self, c_amqp_definitions.delivery_number message_number):
        cdef c_amqpvalue.AMQP_VALUE delivery_state
        delivery_state = c_message.messaging_delivery_accepted()
        if c_message_receiver.messagereceiver_send_message_disposition(self._c_value, self._link_name, message_number, delivery_state) != 0:
            raise RuntimeError("Unable to send message dispostition 'accepted' for message number {}".format(message_number))
        c_amqpvalue.amqpvalue_destroy(delivery_state)

    cpdef settle_released_message(self, c_amqp_definitions.delivery_number message_number):
        cdef c_amqpvalue.AMQP_VALUE delivery_state
        delivery_state = c_message.messaging_delivery_released()
        if c_message_receiver.messagereceiver_send_message_disposition(self._c_value, self._link_name, message_number, delivery_state) != 0:
            raise RuntimeError("Unable to send message dispostition 'released' for message number {}".format(message_number))
        c_amqpvalue.amqpvalue_destroy(delivery_state)

    cpdef settle_rejected_message(self, c_amqp_definitions.delivery_number message_number, const char* error_condition, const char* error_description, AMQPValue error_info=None):
        cdef c_amqpvalue.AMQP_VALUE delivery_state
        cdef c_amqp_definitions.fields delivery_fields
        if error_info is not None:
            delivery_fields = <c_amqp_definitions.fields>error_info._c_value
        else:
            delivery_fields = <c_amqp_definitions.fields>NULL
        delivery_state = c_message.messaging_delivery_rejected(error_condition, error_description, delivery_fields)
        if c_message_receiver.messagereceiver_send_message_disposition(self._c_value, self._link_name, message_number, delivery_state) != 0:
            raise RuntimeError("Unable to send message dispostition 'rejected' for message number {}".format(message_number))
        c_amqpvalue.amqpvalue_destroy(delivery_state)

    cpdef settle_modified_message(self, c_amqp_definitions.delivery_number message_number, bint delivery_failed, bint undeliverable_here, AMQPValue annotations):
        cdef c_amqpvalue.AMQP_VALUE delivery_state
        cdef c_amqp_definitions.fields delivery_fields
        if annotations is not None:
            delivery_fields = <c_amqp_definitions.fields>annotations._c_value
        else:
            delivery_fields = <c_amqp_definitions.fields>NULL
        delivery_state = c_message.messaging_delivery_modified(delivery_failed, undeliverable_here, delivery_fields)
        if c_message_receiver.messagereceiver_send_message_disposition(self._c_value, self._link_name, message_number, delivery_state) != 0:
            raise RuntimeError("Unable to send message dispostition 'delivery-modified' for message number {}".format(message_number))
        c_amqpvalue.amqpvalue_destroy(delivery_state)

    cdef wrap(self, cMessageReceiver value):
        self.destroy()
        self._link = value._link
        self._c_value = value._c_value
        self._validate()

    cpdef set_trace(self, bint value):
        c_message_receiver.messagereceiver_set_trace(self._c_value, value)


#### Callbacks (context is a MessageReceiver instance)

cdef void on_message_receiver_state_changed(void* context, c_message_receiver.MESSAGE_RECEIVER_STATE_TAG new_state, c_message_receiver.MESSAGE_RECEIVER_STATE_TAG previous_state):
    if context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call on_state_changed during garbage collection, please be sure to close or use a context manager")
            return
        context_obj = <object>context
        try:
            context_obj._state_changed(previous_state, new_state)
        except AttributeError:
            _logger.info("Unknown MessageReceiver state changed: %r to %r", previous_state, new_state)


cdef c_amqpvalue.AMQP_VALUE on_message_received(void* context, c_message.MESSAGE_HANDLE message):
    cdef c_message.MESSAGE_HANDLE cloned
    cloned = c_message.message_clone(message)
    wrapped_message = message_factory(cloned)

    if context != NULL:
        context_pyobj = <PyObject*>context
        if context_pyobj.ob_refcnt == 0: # context is being garbage collected, skip the callback
            _logger.warning("Can't call _message_received during garbage collection")
            return <c_amqpvalue.AMQP_VALUE>NULL
        context_obj = <object>context
        if hasattr(context_obj, '_message_received'):
            context_obj._message_received(wrapped_message)
    return <c_amqpvalue.AMQP_VALUE>NULL
