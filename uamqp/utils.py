#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import uuid
from datetime import timedelta
import time
import base64

from uamqp import c_uamqp


def parse_connection_string(connect_str):
    """Parse a connection string such as those provided by the Azure portal.
    Connection string should be formatted like: `Key=Value;Key=Value;Key=Value`.
    The connection string will be parsed into a dictionary.

    :param connect_str: The connection string.
    :type connect_str: str
    :rtype: dict[str, str]
    """
    connect_info = {}
    fields = connect_str.split(';')
    for field in fields:
        key, value = field.split('=', 1)
        connect_info[key] = value
    return connect_info


def create_sas_token(key_name, shared_access_key, scope, expiry=timedelta(hours=1)):
    """Create a SAS token.

    :param key_name: The username/key name/policy name for the token.
    :type key_name: bytes
    :param shared_access_key: The shared access key to generate the token from.
    :type shared_access_key: bytes
    :param scope: The token permissions scope.
    :type scope: bytes
    :param expiry: The lifetime of the generated token. Default is 1 hour.
    :type expiry: ~datetime.timedelta
    :rtype: bytes
    """
    shared_access_key = base64.b64encode(shared_access_key)
    abs_expiry = int(time.time()) + expiry.seconds
    return c_uamqp.create_sas_token(shared_access_key, scope, key_name, abs_expiry)


def data_factory(value, encoding='UTF-8'):
    """Wrap a Python type in the equivalent C AMQP type.
    If the Python type has already been wrapped in a ~uamqp.types.AMQPType
    object - then this will be used to select the appropriate C type.
    - bool => c_uamqp.BoolValue
    - int => c_uamqp.IntValue
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
    elif isinstance(value, str):
        result = c_uamqp.string_value(value.encode(encoding))
    elif isinstance(value, bytes):
        result = c_uamqp.string_value(value)
    elif isinstance(value, uuid.UUID):
        result = c_uamqp.uuid_value(value)
    elif isinstance(value, bytearray):
        result = c_uamqp.binary_value(value)
    elif isinstance(value, float):
        result = c_uamqp.double_value(value)
    elif isinstance(value, int):
        result = c_uamqp.int_value(value)
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
    return result
