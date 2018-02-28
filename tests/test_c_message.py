#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import pytest

root_path = os.path.realpath('.')
sys.path.append(root_path)

from uamqp import c_uamqp


def test_message():
    value = c_uamqp.create_message()
    new_value = value.clone()
    assert new_value is not value

    #assert isinstance(value.header, c_uamqp.cHeader)
    #assert isinstance(value.properties, c_uamqp.Properties)
    #assert isinstance(value.application_properties, c_uamqp.AMQPValue)
    #assert isinstance(value.message_annotations, c_uamqp.MessageAnnotations)
    #assert isinstance(value.delivery_annotations, c_uamqp.DeliveryAnnotations)
    #assert isinstance(value.footer, c_uamqp.Annotations)

    assert value.message_format == 0
    assert value.body_type == c_uamqp.MessageBodyType.NoneType


def test_body_value():
    message = c_uamqp.create_message()
    body_value = c_uamqp.string_value(b'TestBodyValue')

    message.set_body_value(body_value)
    assert message.body_type == c_uamqp.MessageBodyType.ValueType
    
    body = message.get_body_value()
    assert body.type == c_uamqp.AMQPType.StringValue


def test_body_sequence():
    message = c_uamqp.create_message()
    message.add_body_sequence(c_uamqp.int_value(1))
    message.add_body_sequence(c_uamqp.int_value(2))
    message.add_body_sequence(c_uamqp.int_value(3))

    assert message.count_body_sequence() == 3
    assert message.body_type == c_uamqp.MessageBodyType.SequenceType

    seq_value = message.get_body_sequence(2)
    assert seq_value.type == c_uamqp.AMQPType.IntValue
    assert seq_value.value == 3