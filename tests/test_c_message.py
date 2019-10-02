#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import pytest

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


def test_delivery_tag():
    message = c_uamqp.create_message()
    assert not message.delivery_tag
