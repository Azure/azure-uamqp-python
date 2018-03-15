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


class AMQPType:

    def __init__(self, value):
        self._c_type = self._c_wrapper(value)

    @property
    def value(self):
        return self._c_type.value

    @property
    def c_data(self):
        return self._c_type

    def _c_wrapper(self, value):
        raise NotImplementedError()


class AMQPSymbol(AMQPType):

    def __init__(self, value, encoding='UTF-8'):
        self._c_type = self._c_wrapper(value, encoding)

    def _c_wrapper(self, value, encoding):
        value = value.encode(encoding) if isinstance(value, str) else value
        return c_uamqp.symbol_value(value)


class AMQPLong(AMQPType):

    _min_value = -2147483647
    _max_value = 2147438647

    def _c_wrapper(self, value):
        try:
            value = int(value)
            assert value > self._min_value and value < self._max_value
        except (TypeError, AssertionError):
            error = "Value must be an integer between {} and {}".format(
                self._min_value, self._max_value)
            raise ValueError(error)
        return c_uamqp.long_value(int(value))
