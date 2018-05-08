#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# pylint: disable=super-init-not-called,arguments-differ

from uamqp import c_uamqp


class AMQPType:
    """Base type for specific AMQP encoded type definitions.

    :ivar value: The Python value of the AMQP type.
    :ivar c_data: The C AMQP encoded object.
    """

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
    """An AMQP symbol object.

    :ivar value: The Python value of the AMQP type.
    :vartype value: bytes
    :ivar c_data: The C AMQP encoded object.
    :vartype c_data: c_uamqp.SymbolValue
    :param value: The value to encode as an AMQP symbol.
    :type value: bytes or str
    :param encoding: The encoding to be used if a str is provided.
     The default is 'UTF-8'.
    :type encoding: str
    """

    def __init__(self, value, encoding='UTF-8'):
        self._c_type = self._c_wrapper(value, encoding)

    def _c_wrapper(self, value, encoding='UTF-8'):
        value = value.encode(encoding) if isinstance(value, str) else value
        return c_uamqp.symbol_value(value)


class AMQPLong(AMQPType):
    """An AMQP long object. The value of a long must be
    between -2147483647 and 2147438647.

    :ivar value: The Python value of the AMQP type.
    :vartype value: int
    :ivar c_data: The C AMQP encoded object.
    :vartype c_data: ~uamqp.c_uamqp.LongValue
    :param value: The value to encode as an AMQP symbol.
    :type value: int
    :raises: ValueError if value is not within allowed range.
    """

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


class AMQPuLong(AMQPType):
    """An AMQP unsigned long object. The value of a long must be
    between 0 and 4294877294.

    :ivar value: The Python value of the AMQP type.
    :vartype value: int
    :ivar c_data: The C AMQP encoded object.
    :vartype c_data: ~uamqp.c_uamqp.ULongValue
    :param value: The value to encode as an AMQP symbol.
    :type value: int
    :raises: ValueError if value is not within allowed range.
    """

    _min_value = 0
    _max_value = 4294877294

    def _c_wrapper(self, value):
        try:
            value = int(value)
            assert value > self._min_value and value < self._max_value
        except (TypeError, AssertionError):
            error = "Value must be an integer between {} and {}".format(
                self._min_value, self._max_value)
            raise ValueError(error)
        return c_uamqp.ulong_value(int(value))
