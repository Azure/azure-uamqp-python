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
cimport c_utils


_logger = logging.getLogger(__name__)


cpdef create_data(char* binary_data):
    cdef c_amqpvalue.AMQP_VALUE body_data
    cdef c_amqpvalue.amqp_binary _binary
    length = len(binary_data)
    _binary.length = length
    _binary.bytes = <void*>binary_data
    body_data = c_amqp_definitions.amqpvalue_create_data(_binary)
    if <void*>body_data == NULL:
        raise ValueError("Unable to create payload data")
    return value_factory(body_data)


cpdef create_sequence(AMQPValue sequence_data):
    body_data = c_amqp_definitions.amqpvalue_create_amqp_sequence(<c_amqpvalue.AMQP_VALUE>sequence_data._c_value)
    if <void*>body_data == NULL:
        raise ValueError("Unable to create payload data")
    return value_factory(body_data)
