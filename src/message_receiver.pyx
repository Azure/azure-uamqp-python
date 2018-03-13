#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
import logging
import functools
import asyncio

# C imports
cimport c_message_receiver
cimport c_message


_logger = logging.getLogger(__name__)


cpdef create_message_receiver(cLink link, callback_context):
    receiver = cMessageReceiver()
    receiver.create(<c_link.LINK_HANDLE>link._c_value, on_message_receiver_state_changed, <void*>callback_context)
    return receiver


cdef class cMessageReceiver(StructBase):

    cdef c_message_receiver.MESSAGE_RECEIVER_HANDLE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        _logger.debug("Deallocating {}".format(self.__class__.__name__))
        self.destroy()

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cdef create(self, c_link.LINK_HANDLE link, c_message_receiver.ON_MESSAGE_RECEIVER_STATE_CHANGED on_message_sender_state_changed, void* context):
        self.destroy()
        self._c_value = c_message_receiver.messagereceiver_create(link, on_message_sender_state_changed, context)
        self._validate()

    cpdef open(self, callback_context):
        if c_message_receiver.messagereceiver_open(self._c_value, <c_message_receiver.ON_MESSAGE_RECEIVED>on_message_received, <void*>callback_context) != 0:
            self._value_error()

    cpdef close(self):
        if c_message_receiver.messagereceiver_close(self._c_value) != 0:
            self._value_error()

    cpdef destroy(self):
        if <void*>self._c_value is not NULL:
            _logger.debug("Destroying {}".format(self.__class__.__name__))
            c_message_receiver.messagereceiver_destroy(self._c_value)
            self._c_value = <c_message_receiver.MESSAGE_RECEIVER_HANDLE>NULL

    cdef wrap(self, c_message_receiver.MESSAGE_RECEIVER_HANDLE value):
        self.destroy()
        self._c_value = value
        self._validate()

    cpdef set_trace(self, bint value):
        c_message_receiver.messagereceiver_set_trace(self._c_value, value)


#### Callbacks

cdef void on_message_receiver_state_changed(void* context, c_message_receiver.MESSAGE_RECEIVER_STATE_TAG new_state, c_message_receiver.MESSAGE_RECEIVER_STATE_TAG previous_state):
    context_obj = <object>context
    context_obj._state_changed(previous_state, new_state)


cdef c_amqpvalue.AMQP_VALUE on_message_received(void* context, c_message.MESSAGE_HANDLE message):
    if context == NULL:
        return c_message.messaging_delivery_accepted()

    context_obj = <object>context
    cdef c_message.MESSAGE_HANDLE cloned
    cloned = c_message.message_clone(message)
    wrapped_message = message_factory(cloned)
    try:
        if hasattr(context_obj, "_message_received_async"):
            asyncio.ensure_future(context_obj._message_received_async(wrapped_message), loop=context_obj.loop)
        else:
            context_obj._message_received(wrapped_message)

    except Exception as e:
        if hasattr(e, 'rejection_description'):
            _logger.debug("Rejecting message")
            error_condition = b"amqp:internal-error"
            return c_message.messaging_delivery_rejected(error_condition, e.rejection_description)

        elif hasattr(e, 'abandoned'):
            if e.annotations is not None:
                _logger.debug("abandoning message with annotations")
                _ann = create_fields(<AMQPValue>e.annotations)
                return c_message.messaging_delivery_modified(True, True,  <c_amqp_definitions.fields>_ann)
            _logger.debug("abandoning message")
            return c_message.messaging_delivery_modified(True, False, <c_amqp_definitions.fields>NULL)

        elif hasattr(e, 'deferred'):
            if e.annotations is not None:
                _logger.debug("deferring message with annotations")
                _ann = create_fields(<AMQPValue>e.annotations)
                return c_message.messaging_delivery_modified(True, True, <c_amqp_definitions.fields>_ann)
            _logger.debug("deferring message")
            return c_message.messaging_delivery_modified(True, True, <c_amqp_definitions.fields>NULL)
        else:
            raise
    return c_message.messaging_delivery_accepted()
