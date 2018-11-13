#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import pytest

from uamqp import c_uamqp


def test_header():
    value = c_uamqp.cHeader()
    assert value is not None


def test_annotations():
    test_value = c_uamqp.bool_value(True)
    value = c_uamqp.create_annotations(test_value)

    # TODO
    #a_map = value.value
    #assert a_map.type == c_uamqp.AMQPType.DictValue

    new_value = value.clone()
    assert new_value is not value


def test_delivery_annotations():
    test_value = c_uamqp.bool_value(True)
    value = c_uamqp.create_delivery_annotations(test_value)

    # TODO
    #a_map = value.value
    #assert a_map.type == c_uamqp.AMQPType.DictValue


def test_message_annotations():
    test_value = c_uamqp.bool_value(True)
    value = c_uamqp.create_message_annotations(test_value)

    # TODO
    #a_map = value.value
    #assert a_map.type == c_uamqp.AMQPType.DictValue




