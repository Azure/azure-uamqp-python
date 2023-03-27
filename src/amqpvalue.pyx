#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

# Python imports
from enum import Enum
import logging
import uuid
import copy


# C improts
from libc cimport stdint
from libc.stdlib cimport malloc, realloc, free
from libc.string cimport memcpy

cimport cython
cimport c_amqpvalue
cimport c_amqp_definitions


_logger = logging.getLogger(__name__)


cdef int encode_bytes_callback(void* context, const unsigned char* encoded_bytes, size_t length):
    context_obj = <object>context
    context_obj.append(encoded_bytes[:length])
    return 0


cdef get_amqp_value_type(c_amqpvalue.AMQP_VALUE value):
    type_val = c_amqpvalue.amqpvalue_get_type(value)
    try:
        return AMQPType(type_val)
    except ValueError:
        _logger.info("Received unrecognized type value: %r", type_val)
        return AMQPType.ErrorType


cpdef enocde_batch_value(AMQPValue value, message_body):
    if c_amqpvalue.amqpvalue_encode(<c_amqpvalue.AMQP_VALUE>value._c_value,
                                     <c_amqpvalue.AMQPVALUE_ENCODER_OUTPUT>encode_bytes_callback,
                                     <void*>message_body) != 0:
        raise ValueError("Failed to encode batched message data.")


class AMQPType(Enum):
    NullValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_NULL
    BoolValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_BOOL
    UByteValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_UBYTE
    UShortValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_USHORT
    UIntValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_UINT
    ULongValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_ULONG
    ByteValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_BYTE
    ShortValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_SHORT
    IntValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_INT
    LongValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_LONG
    FloatValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_FLOAT
    DoubleValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_DOUBLE
    CharValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_CHAR
    TimestampValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_TIMESTAMP
    UUIDValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_UUID
    BinaryValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_BINARY
    StringValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_STRING
    SymbolValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_SYMBOL
    ListValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_LIST
    DictValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_MAP
    ArrayValue = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_ARRAY
    DescribedType = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_DESCRIBED
    CompositeType = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_COMPOSITE
    UnknownType = c_amqpvalue.AMQP_TYPE_TAG.AMQP_TYPE_UNKNOWN
    ErrorType = 999


cdef value_factory(c_amqpvalue.AMQP_VALUE value):
    type_val = get_amqp_value_type(value)
    _logger.debug("Wrapping value type: %r", type_val)
    if type_val == AMQPType.NullValue:
        new_obj = AMQPValue()
    elif type_val == AMQPType.BoolValue:
        new_obj = BoolValue()
    elif type_val == AMQPType.UByteValue:
        new_obj = UByteValue()
    elif type_val == AMQPType.UShortValue:
        new_obj = UShortValue()
    elif type_val == AMQPType.UIntValue:
        new_obj = UIntValue()
    elif type_val == AMQPType.ULongValue:
        new_obj = ULongValue()
    elif type_val == AMQPType.ByteValue:
        new_obj = ByteValue()
    elif type_val == AMQPType.ShortValue:
        new_obj = ShortValue()
    elif type_val == AMQPType.IntValue:
        new_obj = IntValue()
    elif type_val == AMQPType.LongValue:
        new_obj = LongValue()
    elif type_val == AMQPType.FloatValue:
        new_obj = FloatValue()
    elif type_val == AMQPType.DoubleValue:
        new_obj = DoubleValue()
    elif type_val == AMQPType.CharValue:
        new_obj = CharValue()
    elif type_val == AMQPType.TimestampValue:
        new_obj = TimestampValue()
    elif type_val == AMQPType.UUIDValue:
        new_obj = UUIDValue()
    elif type_val == AMQPType.BinaryValue:
        new_obj = BinaryValue()
    elif type_val == AMQPType.StringValue:
        new_obj = StringValue()
    elif type_val == AMQPType.SymbolValue:
        new_obj = SymbolValue()
    elif type_val == AMQPType.ListValue:
        new_obj = ListValue()
    elif type_val == AMQPType.DictValue:
        new_obj = DictValue()
    elif type_val == AMQPType.ArrayValue:  # Do checking
        new_obj = ArrayValue()
    elif type_val == AMQPType.CompositeType:
        new_obj = CompositeValue()
    elif type_val == AMQPType.DescribedType:
        new_obj = DescribedValue()
    else:
        error = "Unrecognized AMQPType: {}".format(type_val)
        _logger.info(error)
        raise TypeError(error)
    new_obj.wrap(value)
    return new_obj


cpdef null_value():
    new_obj = AMQPValue()
    new_obj.create()
    return new_obj


cpdef bool_value(bint value):
    value = 1 if value else 0
    new_obj = BoolValue()
    new_obj.create(value)
    return new_obj


cpdef ubyte_value(unsigned char value):
    new_obj = UByteValue()
    new_obj.create(value)
    return new_obj


cpdef ushort_value(stdint.uint16_t value):
    new_obj = UShortValue()
    new_obj.create(value)
    return new_obj


cpdef uint_value(stdint.uint32_t value):
    new_obj = UIntValue()
    new_obj.create(value)
    return new_obj


cpdef ulong_value(stdint.uint64_t value):
    new_obj = ULongValue()
    new_obj.create(value)
    return new_obj


cpdef byte_value(char value):
    new_obj = ByteValue()
    new_obj.create(value)
    return new_obj


cpdef short_value(stdint.int16_t value):
    new_obj = ShortValue()
    new_obj.create(value)
    return new_obj


cpdef int_value(stdint.int32_t value):
    new_obj = IntValue()
    new_obj.create(value)
    return new_obj


cpdef long_value(stdint.int64_t value):
    new_obj = LongValue()
    new_obj.create(value)
    return new_obj


cpdef float_value(float value):
    new_obj = FloatValue()
    new_obj.create(value)
    return new_obj


cpdef double_value(double value):
    new_obj = DoubleValue()
    new_obj.create(value)
    return new_obj


cpdef char_value(stdint.uint32_t value):
    new_obj = CharValue()
    new_obj.create(value)
    return new_obj


cpdef timestamp_value(stdint.int64_t value):
    new_obj = TimestampValue()
    new_obj.create(value)
    return new_obj


cpdef uuid_value(value):
    if not isinstance(value, uuid.UUID):
        raise TypeError("Input value must be type UUID.")
    new_obj = UUIDValue()
    new_obj.create(<bytes>value.bytes)
    return new_obj


cpdef binary_value(value):
    bytes_value = bytes(value)
    new_obj = BinaryValue()
    new_obj.create(<bytes>bytes_value)
    return new_obj


cpdef string_value(char* value):
    new_obj = StringValue()
    new_obj.create(value)
    return new_obj


cpdef symbol_value(char* value):
    new_obj = SymbolValue()
    new_obj.create(value)
    return new_obj


cpdef list_value():
    new_obj = ListValue()
    new_obj.create()
    return new_obj


cpdef dict_value():
    new_obj = DictValue()
    new_obj.create()
    return new_obj


cpdef array_value():
    new_obj = ArrayValue()
    new_obj.create()
    return new_obj


cpdef described_value(AMQPValue descriptor, AMQPValue value):
    new_obj = DescribedValue()
    new_obj.create(descriptor, value)
    return new_obj


cdef class AMQPValue(StructBase):

    _type = AMQPType.NullValue
    cdef c_amqpvalue.AMQP_VALUE _c_value

    def __cinit__(self):
        pass

    def __dealloc__(self):
        if _logger:
            _logger.debug("Deallocating %r", self.__class__.__name__)
        self.destroy()

    def __eq__(self, AMQPValue other):
        return c_amqpvalue.amqpvalue_are_equal(self._c_value, other._c_value)

    def __ne__(self, AMQPValue other):
        return not c_amqpvalue.amqpvalue_are_equal(self._c_value, other._c_value)

    def __bytes__(self):
        return self._as_string()

    def __str__(self):
        as_bytes = self._as_string()
        return str(as_bytes, encoding="UTF-8", errors="ignore" )

    def __unicode__(self):
        as_bytes = self._as_string()
        try:
            return str(as_bytes.decode('UTF-8'))
        except UnicodeDecodeError:
            return str(as_bytes)

    cpdef _as_string(self):
        cdef c_amqpvalue.AMQP_VALUE value
        cdef const char* as_string
        value = c_amqpvalue.amqpvalue_clone(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        as_string = c_amqpvalue.amqpvalue_to_string(value)
        py_string = <bytes> as_string
        free(as_string)
        c_amqpvalue.amqpvalue_destroy(self._c_value)
        return py_string

    cdef _validate(self):
        if <void*>self._c_value is NULL:
            self._memory_error()

    cpdef destroy(self):
        try:
            if <void*>self._c_value is not NULL:
                if _logger:
                    _logger.debug("Destroying %r", self.__class__.__name__)
                c_amqpvalue.amqpvalue_destroy(self._c_value)
        except KeyboardInterrupt:
            pass
        finally:
            self._c_value = <c_amqpvalue.AMQP_VALUE>NULL

    cdef wrap(self, c_amqpvalue.AMQP_VALUE value):
        self.destroy()
        self._c_value = value
        self._validate()

    def create(self):
        new_value = c_amqpvalue.amqpvalue_create_null()
        self.wrap(new_value)

    @property
    def type(self):
        if <void*>self._c_value is NULL:
            self._null_error()
        obj_type = get_amqp_value_type(self._c_value)
        return obj_type

    @property
    def value(self):
        return None

    cpdef get_encoded_size(self):
        cdef size_t length
        if c_amqpvalue.amqpvalue_get_encoded_size(self._c_value, &length) != 0:
            self._value_error("Failed to get encoded size.")
        return length

    cpdef clone(self):
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_clone(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        return value_factory(value)


cdef class BoolValue(AMQPValue):

    _type = AMQPType.BoolValue

    cpdef _bool_value(self):
        cdef bint _value
        if c_amqpvalue.amqpvalue_get_boolean(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()

    def create(self, bint value):
        new_value = c_amqpvalue.amqpvalue_create_boolean(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        str_value = str(self)
        if str_value in ["false"]:
            return False
        elif str_value in ["true"]:
            return True
        else:
            self._value_error()


cdef class UByteValue(AMQPValue):

    _type = AMQPType.UByteValue

    def create(self, unsigned char value):
        new_value = c_amqpvalue.amqpvalue_create_ubyte(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef unsigned char _value
        if c_amqpvalue.amqpvalue_get_ubyte(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class UShortValue(AMQPValue):

    _type = AMQPType.UShortValue

    def create(self, stdint.uint16_t value):
        new_value = c_amqpvalue.amqpvalue_create_ushort(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.uint16_t _value
        if c_amqpvalue.amqpvalue_get_ushort(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class UIntValue(AMQPValue):

    _type = AMQPType.UIntValue

    def create(self, stdint.uint32_t value):
        new_value = c_amqpvalue.amqpvalue_create_uint(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_uint(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class ULongValue(AMQPValue):

    _type = AMQPType.ULongValue

    def create(self, stdint.uint64_t value):
        new_value = c_amqpvalue.amqpvalue_create_ulong(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.uint64_t _value
        if c_amqpvalue.amqpvalue_get_ulong(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class ByteValue(AMQPValue):

    _type = AMQPType.ByteValue

    def create(self, char value):
        new_value = c_amqpvalue.amqpvalue_create_byte(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef char _value
        if c_amqpvalue.amqpvalue_get_byte(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class ShortValue(AMQPValue):

    _type = AMQPType.ShortValue

    def create(self, stdint.int16_t value):
        new_value = c_amqpvalue.amqpvalue_create_short(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.int16_t _value
        if c_amqpvalue.amqpvalue_get_short(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class IntValue(AMQPValue):

    _type = AMQPType.IntValue

    def create(self, stdint.int32_t value):
        new_value = c_amqpvalue.amqpvalue_create_int(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.int32_t _value
        if c_amqpvalue.amqpvalue_get_int(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class LongValue(AMQPValue):

    _type = AMQPType.LongValue

    def create(self, stdint.int64_t value):
        new_value = c_amqpvalue.amqpvalue_create_long(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.int64_t _value
        if c_amqpvalue.amqpvalue_get_long(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class FloatValue(AMQPValue):

    _type = AMQPType.FloatValue

    def create(self, float value):
        new_value = c_amqpvalue.amqpvalue_create_float(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef float _value
        if c_amqpvalue.amqpvalue_get_float(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class DoubleValue(AMQPValue):

    _type = AMQPType.DoubleValue

    def create(self, double value):
        new_value = c_amqpvalue.amqpvalue_create_double(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef double _value
        if c_amqpvalue.amqpvalue_get_double(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class CharValue(AMQPValue):

    _type = AMQPType.CharValue

    def create(self, stdint.uint32_t value):
        new_value = c_amqpvalue.amqpvalue_create_char(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_char(self._c_value, &_value) == 0:
            return chr(_value)
        else:
            self._value_error()


cdef class TimestampValue(AMQPValue):

    _type = AMQPType.TimestampValue

    def create(self, stdint.int64_t value):
        new_value = c_amqpvalue.amqpvalue_create_timestamp(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef stdint.int64_t _value
        if c_amqpvalue.amqpvalue_get_timestamp(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()


cdef class UUIDValue(AMQPValue):

    _type = AMQPType.UUIDValue

    def create(self, bytes value):
        new_value = c_amqpvalue.amqpvalue_create_uuid(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        str_val = str(self)
        return uuid.UUID(str_val)  # TODO: Get proper value


cdef class BinaryValue(AMQPValue):

    _type = AMQPType.BinaryValue

    def create(self, bytes value):
        cdef c_amqpvalue.amqp_binary _binary
        length = len(list(value))
        _binary.length = length
        _binary.bytes = <char*>value
        new_value = c_amqpvalue.amqpvalue_create_binary(_binary)
        self.wrap(new_value)

    def __len__(self):
        assert self.type
        cdef c_amqpvalue.amqp_binary _value
        if c_amqpvalue.amqpvalue_get_binary(self._c_value, &_value) == 0:
            return _value.length
        else:
            self._value_error()

    @property
    def value(self):
        assert self.type
        cdef c_amqpvalue.amqp_binary _value
        cdef char* bytes_value
        if c_amqpvalue.amqpvalue_get_binary(self._c_value, &_value) == 0:
            bytes_value = <char*>_value.bytes
            return bytes_value[:_value.length]
        else:
            self._value_error()


cdef class StringValue(AMQPValue):

    _type = AMQPType.StringValue

    def create(self, char* value):
        new_value = c_amqpvalue.amqpvalue_create_string(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef const char* _value
        if c_amqpvalue.amqpvalue_get_string(self._c_value, &_value) == 0:
            return copy.deepcopy(_value)
        else:
            self._value_error()


cdef class SymbolValue(AMQPValue):

    _type = AMQPType.SymbolValue

    def create(self, char* value):
        new_value = c_amqpvalue.amqpvalue_create_symbol(value)
        self.wrap(new_value)

    @property
    def value(self):
        assert self.type
        cdef const char* _value
        if c_amqpvalue.amqpvalue_get_symbol(self._c_value, &_value) == 0:
            return copy.deepcopy(_value)
        else:
            self._value_error()


cdef class ListValue(AMQPValue):

    _type = AMQPType.ListValue

    def create(self):
        new_value = c_amqpvalue.amqpvalue_create_list()
        self.wrap(new_value)

    def __len__(self):
        return self.size

    def __getitem__(self, size_t index):
        if index >= self.size:
            raise IndexError("Index is out of range.")
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_get_list_item(self._c_value, index)
        if <void*>value == NULL:
            self._value_error()
        try:
            return value_factory(value)
        except TypeError:
            return None

    def __setitem__(self, stdint.uint32_t index, AMQPValue value):
        assert value.type
        if index >= self.size:
            raise IndexError("Index is out of range.")
        if c_amqpvalue.amqpvalue_set_list_item(self._c_value, index, value._c_value) != 0:
            self._value_error()

    @property
    def size(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_list_item_count(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()

    @size.setter
    def size(self, stdint.uint32_t length):
        assert self.type
        if c_amqpvalue.amqpvalue_set_list_item_count(self._c_value, length) != 0:
            self._value_error()

    @property
    def value(self):
        assert self.type
        value = []
        for i in range(self.size):
            value.append(copy.deepcopy(self[i].value))
        return value


cdef class DictValue(AMQPValue):

    _type = AMQPType.DictValue

    def create(self):
        new_value = c_amqpvalue.amqpvalue_create_map()
        self.wrap(new_value)

    def __len__(self):
        return self.size

    def __getitem__(self, AMQPValue key):
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_get_map_value(self._c_value, key._c_value)
        if <void*>value == NULL:
            raise KeyError("No value found for key: {}".format(key.value))
        try:
            return value_factory(value)
        except TypeError:
            return None

    def __setitem__(self, AMQPValue key, AMQPValue value):
        if c_amqpvalue.amqpvalue_set_map_value(self._c_value, key._c_value, value._c_value) != 0:
            self._value_error()

    def get(self, stdint.uint32_t index):
        if index >= self.size:
            raise IndexError("Index is out of range.")
        cdef c_amqpvalue.AMQP_VALUE key
        cdef c_amqpvalue.AMQP_VALUE value
        if c_amqpvalue.amqpvalue_get_map_key_value_pair(self._c_value, index, &key,  &value) != 0:
            self._value_error()
        return (value_factory(key), value_factory(value))

    @property
    def size(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_map_pair_count(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()

    @property
    def value(self):
        assert self.type
        value = {}
        for i in range(self.size):
            key, item = self.get(i)
            value[copy.deepcopy(key.value)] = copy.deepcopy(item.value)
        return value


cdef class ArrayValue(AMQPValue):

    _type = AMQPType.ArrayValue

    def create(self):
        self._c_value = c_amqpvalue.amqpvalue_create_array()
        self._validate()

    def __len__(self):
        return self.size

    def __getitem__(self, stdint.uint32_t index):
        if index >= self.size:
            raise IndexError("Index is out of range.")
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_get_array_item(self._c_value, index)
        if <void*>value == NULL:
            self._value_error()
        return value_factory(value)

    @property
    def size(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_array_item_count(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()

    cpdef append(self, AMQPValue value):
        assert self.type
        cdef c_amqpvalue.AMQP_VALUE _value
        _value = <c_amqpvalue.AMQP_VALUE>value._c_value
        if c_amqpvalue.amqpvalue_add_array_item(self._c_value, <c_amqpvalue.AMQP_VALUE>value._c_value) != 0:
            self._value_error()

    @property
    def value(self):
        assert self.type
        value = []
        for i in range(self.size):
            value.append(copy.deepcopy(self[i].value))
        return value


cdef class CompositeValue(AMQPValue):

    _type = AMQPType.CompositeType

    def create(self, AMQPValue descriptor, stdint.uint32_t list_size):
        new_value = c_amqpvalue.amqpvalue_create_composite(descriptor._c_value, list_size)
        self.wrap(new_value)

    def create_from_long(self, stdint.uint64_t descriptor):
        new_value = c_amqpvalue.amqpvalue_create_composite_with_ulong_descriptor(descriptor)
        self.wrap(new_value)

    def __len__(self):
        return self.size

    def __getitem__(self, stdint.uint32_t index):
        if index >= self.size:
            raise IndexError("Index is out of range.")
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_get_composite_item(self._c_value, index)
        if <void*>value == NULL:
            self._value_error()
        try:
            return value_factory(value)
        except TypeError:
            raise IndexError("No item found at index {}".format(index))

    def __setitem__(self, stdint.uint32_t index, AMQPValue value):
        assert value.type
        if index >= self.size:
            raise IndexError("Index is out of range.")
        if c_amqpvalue.amqpvalue_set_composite_item(self._c_value, index, value._c_value) != 0:
            self._value_error()

    @property
    def size(self):
        assert self.type
        cdef stdint.uint32_t _value
        if c_amqpvalue.amqpvalue_get_composite_item_count(self._c_value, &_value) == 0:
            return _value
        else:
            self._value_error()

    def pop(self, stdint.uint32_t index):
        if index >= self.size:
            raise IndexError("Index is out of range.")
        cdef c_amqpvalue.AMQP_VALUE value
        value = c_amqpvalue.amqpvalue_get_composite_item(self._c_value, index)
        if <void*>value == NULL:
            self._value_error()
        try:
            return value_factory(value)
        except TypeError:
            raise IndexError("No item found at index {}".format(index))


cdef class DescribedValue(AMQPValue):

    _type = AMQPType.DescribedType

    def create(self, AMQPValue descriptor, AMQPValue value):
        cdef c_amqpvalue.AMQP_VALUE cloned_descriptor
        cdef c_amqpvalue.AMQP_VALUE cloned_value
        cloned_descriptor = c_amqpvalue.amqpvalue_clone(<c_amqpvalue.AMQP_VALUE>descriptor._c_value)
        if <void*>cloned_descriptor == NULL:
            self._value_error()
        cloned_value = c_amqpvalue.amqpvalue_clone(<c_amqpvalue.AMQP_VALUE>value._c_value)
        if <void*>cloned_value == NULL:
            self._value_error()
        new_value = c_amqpvalue.amqpvalue_create_described(cloned_descriptor, cloned_value)
        self.wrap(new_value)

    @property
    def description(self):
        cdef c_amqpvalue.AMQP_VALUE value
        cdef c_amqpvalue.AMQP_VALUE cloned
        value = c_amqpvalue.amqpvalue_get_inplace_descriptor(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        cloned = c_amqpvalue.amqpvalue_clone(value)
        if <void*>cloned == NULL:
            self._value_error()
        return value_factory(cloned)

    @property
    def data(self):
        cdef c_amqpvalue.AMQP_VALUE value
        cdef c_amqpvalue.AMQP_VALUE cloned
        value = c_amqpvalue.amqpvalue_get_inplace_described_value(self._c_value)
        if <void*>value == NULL:
            self._value_error()
        cloned = c_amqpvalue.amqpvalue_clone(value)
        if <void*>cloned == NULL:
            self._value_error()
        return value_factory(cloned)

    @property
    def value(self):
        assert self.type
        #descriptor = self.description
        described = self.data
        return copy.deepcopy(described.value)
