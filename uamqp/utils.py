#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import calendar
import uuid
import logging
from datetime import datetime

import six
from uamqp import c_uamqp

logger = logging.getLogger(__name__)


def _convert_py_number(value):
    """Convert a Python integer value into equivalent C object.
    Will attempt to use the smallest possible conversion, starting with int, then long
    then double.
    """
    try:
        return c_uamqp.int_value(value)
    except OverflowError:
        pass
    try:
        return c_uamqp.long_value(value)
    except OverflowError:
        pass
    return c_uamqp.double_value(value)


def data_factory(value, encoding='UTF-8'):
    """Wrap a Python type in the equivalent C AMQP type.
    If the Python type has already been wrapped in a ~uamqp.types.AMQPType
    object - then this will be used to select the appropriate C type.
    - bool => c_uamqp.BoolValue
    - int => c_uamqp.IntValue, LongValue, DoubleValue
    - str => c_uamqp.StringValue
    - bytes => c_uamqp.BinaryValue
    - list/set/tuple => c_uamqp.ListValue
    - dict => c_uamqp.DictValue (AMQP map)
    - float => c_uamqp.DoubleValue
    - uuid.UUID => c_uamqp.UUIDValue

    :param value: The value to wrap.
    :type value: ~uamqp.types.AMQPType
    :rtype: uamqp.c_uamqp.AMQPValue
    """
    result = None
    if value is None:
        result = c_uamqp.null_value()
    elif hasattr(value, 'c_data'):
        result = value.c_data
    elif isinstance(value, c_uamqp.AMQPValue):
        result = value
    elif isinstance(value, bool):
        result = c_uamqp.bool_value(value)
    elif isinstance(value, six.text_type):
        result = c_uamqp.string_value(value.encode(encoding))
    elif isinstance(value, six.binary_type):
        result = c_uamqp.string_value(value)
    elif isinstance(value, uuid.UUID):
        result = c_uamqp.uuid_value(value)
    elif isinstance(value, bytearray):
        result = c_uamqp.binary_value(value)
    elif isinstance(value, six.integer_types):
        result = _convert_py_number(value)
    elif isinstance(value, float):
        result = c_uamqp.double_value(value)
    elif isinstance(value, dict):
        wrapped_dict = c_uamqp.dict_value()
        for key, item in value.items():
            wrapped_dict[data_factory(key, encoding=encoding)] = data_factory(item, encoding=encoding)
        result = wrapped_dict
    elif isinstance(value, (list, set, tuple)):
        wrapped_list = c_uamqp.list_value()
        wrapped_list.size = len(value)
        for index, item in enumerate(value):
            wrapped_list[index] = data_factory(item, encoding=encoding)
        result = wrapped_list
    elif isinstance(value, datetime):
        timestamp = int((calendar.timegm(value.utctimetuple()) * 1000) + (value.microsecond/1000))
        result = c_uamqp.timestamp_value(timestamp)
    return result
