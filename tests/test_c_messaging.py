#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import pytest

from uamqp import c_uamqp

def test_create_source():
    address = b"Address"
    addr_value = c_uamqp.Messaging.create_source(address)

    assert isinstance(addr_value, c_uamqp.AMQPValue)
    assert addr_value.type == c_uamqp.AMQPType.CompositeType
    assert addr_value.size == 1
    assert addr_value[0].value == b"Address"


def test_create_target():
    address = b"Address"
    addr_value = c_uamqp.Messaging.create_target(address)

    assert isinstance(addr_value, c_uamqp.AMQPValue)
    assert addr_value.type == c_uamqp.AMQPType.CompositeType
    assert addr_value.size == 1
    assert addr_value[0].value == b"Address"
    assert str(addr_value[0]) == "Address"


def test_delivery_received():
    rec_value = c_uamqp.Messaging.delivery_received(0, 0)
    assert isinstance(rec_value, c_uamqp.AMQPValue)
    assert rec_value.type == c_uamqp.AMQPType.CompositeType
    assert rec_value.size == 2
    assert rec_value[0].type == c_uamqp.AMQPType.UIntValue
    assert rec_value[0].value == 0
    assert rec_value[1].type == c_uamqp.AMQPType.ULongValue
    assert rec_value[1].value == 0


def test_delivery_accepted():
    acc_val = c_uamqp.Messaging.delivery_accepted()
    assert acc_val.type == c_uamqp.AMQPType.CompositeType
    assert acc_val.size == 0


def test_delivery_rejected():
    rej_val = c_uamqp.Messaging.delivery_rejected(b'Failed', b'Test failure')
    assert rej_val.type == c_uamqp.AMQPType.CompositeType
    assert rej_val.size == 1
    assert rej_val[0].type == c_uamqp.AMQPType.CompositeType
    assert rej_val[0].size == 2
    assert str(rej_val[0][0]) == 'Failed'
    assert str(rej_val[0][1]) == 'Test failure'

    error = c_uamqp.dict_value()
    error_key = c_uamqp.string_value(b"key123")
    error_value = c_uamqp.string_value(b"value456")
    error[error_key] = error_value
    error_info = c_uamqp.create_fields(error)

    rej_val = c_uamqp.Messaging.delivery_rejected(b'Failed', b'Test failure', error_info)
    assert rej_val.type == c_uamqp.AMQPType.CompositeType
    assert rej_val.size == 1
    assert rej_val[0].type == c_uamqp.AMQPType.CompositeType
    assert rej_val[0].size == 3
    assert str(rej_val[0][0]) == 'Failed'
    assert str(rej_val[0][1]) == 'Test failure'
    error_info = rej_val[0][2]
    assert error_info.type == c_uamqp.AMQPType.DictValue
    assert error_info[error_key] == error_value


def test_delivery_released():
    rel_val = c_uamqp.Messaging.delivery_released()
    assert rel_val.type == c_uamqp.AMQPType.CompositeType
    assert rel_val.size == 0


def test_delivery_modified():
    failed_val = c_uamqp.string_value(b"Failed")
    fields = c_uamqp.create_fields(failed_val)
    mod_val = c_uamqp.Messaging.delivery_modified(True, False, fields)
    assert mod_val.type == c_uamqp.AMQPType.CompositeType
    assert mod_val.size == 3
    assert mod_val[0].type == c_uamqp.AMQPType.BoolValue
    assert mod_val[0].value == True
    #assert mod_val[1].type == c_uamqp.AMQPType.BoolValue
    #assert mod_val[1].value == False
    assert mod_val[2].type == c_uamqp.AMQPType.StringValue
