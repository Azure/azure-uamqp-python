#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import calendar
import struct
import uuid
from datetime import datetime
from typing import Iterable, Union, Tuple, Dict

from .types import AMQPTypes, ConstructorBytes, TYPE, VALUE

import six


def _bytes(value, length=1, signed=False):
    # type: (int, int, bool) -> bytes
    return value.to_bytes(length, 'big', signed=signed)


def _construct(byte, construct):
    # type: (bytes, bool) -> bytes
    return byte if construct else b''


def encode_null(output, *args, **kwargs):
    # type: (bytes, Any, Any) -> bytes
    """
    encoding code="0x40" category="fixed" width="0" label="the null value"
    """
    return output + ConstructorBytes.null


def encode_boolean(output, value, with_constructor=True, **kwargs):
    # type: (bytes, bool, bool, Any) -> bytes
    """
    <encoding name="true" code="0x41" category="fixed" width="0" label="the boolean value true"/>
    <encoding name="false" code="0x42" category="fixed" width="0" label="the boolean value false"/>
    <encoding code="0x56" category="fixed" width="1" label="boolean with the octet 0x00 being false and octet 0x01 being true"/>
    """
    value = bool(value)
    if with_constructor:
        output += _construct(ConstructorBytes.bool, with_constructor)
        if value:
            return output + b'\x01'
        else:
            return output + b'\x00'   
    if value:
        return output + ConstructorBytes.bool_true
    else:
        return output + ConstructorBytes.bool_false


def encode_ubyte(output, value, with_constructor=True, **kwargs):
    # type: (bytes, Union[int, bytes], bool, Any) -> bytes
    """
    <encoding code="0x50" category="fixed" width="1" label="8-bit unsigned integer"/>
    """
    try:
        value = int(value)
    except ValueError:
        value = ord(value)
    try:
        output += _construct(ConstructorBytes.ubyte, with_constructor)
        return output + _bytes(abs(value))
    except OverflowError:
        raise ValueError("Unsigned byte value must be 0-255")


def encode_ushort(output, value, with_constructor=True, **kwargs):
    # type: (bytes, Union[int, bytes], bool, Any) -> bytes
    """
    <encoding code="0x60" category="fixed" width="2" label="16-bit unsigned integer in network byte order"/>
    """
    try:
        value = int(value)
    except ValueError:
        value = int.from_bytes(value, 'big')
    try:
        output += _construct(ConstructorBytes.ushort, with_constructor)
        return output + _bytes(abs(value), length=2)
    except OverflowError:
        raise ValueError("Unsigned byte value must be 0-65535")
 

def encode_uint(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Union[int, bytes], bool, bool) -> bytes
    """
    <encoding name="uint0" code="0x43" category="fixed" width="0" label="the uint value 0"/>
    <encoding name="smalluint" code="0x52" category="fixed" width="1" label="unsigned integer value in the range 0 to 255 inclusive"/>
    <encoding code="0x70" category="fixed" width="4" label="32-bit unsigned integer in network byte order"/>
    """
    try:
        value = int(value)
    except ValueError:
        value = int.from_bytes(value, 'big')
    if value == 0:
        return output + ConstructorBytes.uint_0
    try:
        if use_smallest and value <= 255:
            output += _construct(ConstructorBytes.uint_small, with_constructor)
            return output + _bytes(abs(value))
        output += _construct(ConstructorBytes.uint_large, with_constructor)
        return output + _bytes(abs(value), length=4)
    except OverflowError:
        raise ValueError("Value supplied for unsigned int invalid: {}".format(value))


def encode_ulong(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, int, bool, bool) -> bytes
    """
    <encoding name="ulong0" code="0x44" category="fixed" width="0" label="the ulong value 0"/>
    <encoding name="smallulong" code="0x53" category="fixed" width="1" label="unsigned long value in the range 0 to 255 inclusive"/>
    <encoding code="0x80" category="fixed" width="8" label="64-bit unsigned integer in network byte order"/>
    """
    try:
        try:
            value = long(value)
        except NameError:
            value = int(value)
    except ValueError:
        value = int.from_bytes(value, 'big')
    if value == 0:
        return output + ConstructorBytes.ulong_0
    try:
        if use_smallest and value <= 255:
            output += _construct(ConstructorBytes.ulong_small, with_constructor)
            return output + _bytes(abs(value))
        output += _construct(ConstructorBytes.ulong_large, with_constructor)
        return output + _bytes(abs(value), length=8)
    except OverflowError:
        raise ValueError("Value supplied for unsigned long invalid: {}".format(value))


def encode_byte(output, value, with_constructor=True, **kwargs):
    # type: (bytes, int, bool, Any) -> bytes
    """
    <encoding code="0x51" category="fixed" width="1" label="8-bit two's-complement integer"/>
    """
    value = int(value)
    try:
        output += _construct(ConstructorBytes.byte, with_constructor)
        return output + _bytes(value, signed=True)
    except OverflowError:
        raise ValueError("Byte value must be -128-127")


def encode_short(output, value, with_constructor=True, **kwargs):
    # type: (bytes, int, bool, Any) -> bytes
    """
    <encoding code="0x61" category="fixed" width="2" label="16-bit two's-complement integer in network byte order"/>
    """
    value = int(value)
    try:
        output += _construct(ConstructorBytes.short, with_constructor)
        return output + _bytes(value, length=2, signed=True)
    except OverflowError:
        raise ValueError("Short value must be -32768-32767")


def encode_int(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, int, bool, bool) -> bytes
    """
    <encoding name="smallint" code="0x54" category="fixed" width="1" label="8-bit two's-complement integer"/>
    <encoding code="0x71" category="fixed" width="4" label="32-bit two's-complement integer in network byte order"/>
    """
    value = int(value)
    try:
        if use_smallest and (-128 <= value <= 127):
            output += _construct(ConstructorBytes.int_small, with_constructor)
            return output + _bytes(value, signed=True)
        output += _construct(ConstructorBytes.int_large, with_constructor)
        return output + _bytes(value, length=4, signed=True)
    except OverflowError:
        raise ValueError("Value supplied for int invalid: {}".format(value))


def encode_long(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, int, bool, bool) -> bytes
    """
    <encoding name="smalllong" code="0x55" category="fixed" width="1" label="8-bit two's-complement integer"/>
    <encoding code="0x81" category="fixed" width="8" label="64-bit two's-complement integer in network byte order"/>
    """
    try:
        value = long(value)
    except NameError:
        value = int(value)
    try:
        if use_smallest and (-128 <= value <= 127):
            output += _construct(ConstructorBytes.long_small, with_constructor)
            return output + _bytes(value, signed=True)
        output += _construct(ConstructorBytes.long_large, with_constructor)
        return output + _bytes(value, length=8, signed=True)
    except OverflowError:
        raise ValueError("Value supplied for long invalid: {}".format(value))

def encode_float(output, value, with_constructor=True, **kwargs):
    # type: (bytes, float, bool, Any) -> bytes
    """
    <encoding name="ieee-754" code="0x72" category="fixed" width="4" label="IEEE 754-2008 binary32"/>
    """
    value = float(value)
    output += _construct(ConstructorBytes.float, with_constructor)
    return output + struct.pack('>f', value)


def encode_double(output, value, with_constructor=True, **kwargs):
    # type: (bytes, float, bool, Any) -> bytes
    """
    <encoding name="ieee-754" code="0x82" category="fixed" width="8" label="IEEE 754-2008 binary64"/>
    """
    value = float(value)
    output += _construct(ConstructorBytes.double, with_constructor)
    return output + struct.pack('>d', value)


def encode_timestamp(output, value, with_constructor=True, **kwargs):
    # type: (bytes, Union[int, datetime], bool, Any) -> bytes
    """
    <encoding name="ms64" code="0x83" category="fixed" width="8" label="64-bit two's-complement integer representing milliseconds since the unix epoch"/>
    """
    if isinstance(value, datetime):
        value = (calendar.timegm(value.utctimetuple()) * 1000) + (value.microsecond/1000)
    value = int(value)
    output += _construct(ConstructorBytes.timestamp, with_constructor)
    return output + _bytes(value, length=8, signed=True)


def encode_uuid(output, value, with_constructor=True, **kwargs):
    # type: (bytes, Union[uuid.UUID, str, bytes], bool, Any) -> bytes
    """
    <encoding code="0x98" category="fixed" width="16" label="UUID as defined in section 4.1.2 of RFC-4122"/>
    """
    if isinstance(value, six.text_type):
        value = uuid.UUID(value).bytes
    elif isinstance(value, uuid.UUID):
        value = value.bytes
    elif isinstance(value, six.binary_type):
        value = uuid.UUID(bytes=value).bytes
    else:
        raise TypeError("Invalid UUID type: {}".format(type(value)))
    output += _construct(ConstructorBytes.uuid, with_constructor)
    return output + value


def encode_binary(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Union[bytes, bytearray], bool, bool)
    """
    <encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>
    <encoding name="vbin32" code="0xb0" category="variable" width="4" label="up to 2^32 - 1 octets of binary data"/>
    """
    length = len(value)
    if use_smallest and length <= 255:
        output += _construct(ConstructorBytes.binary_small, with_constructor)
        output += _bytes(length)
        return output + value
    try:
        output += _construct(ConstructorBytes.binary_large, with_constructor)
        output += _bytes(length, length=4)
        return output + value
    except OverflowError:
        raise ValueError("Binary data to long to encode")


def encode_string(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Union[bytes, str], bool, bool)
    """
    <encoding name="str8-utf8" code="0xa1" category="variable" width="1" label="up to 2^8 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>
    <encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>
    """
    if isinstance(value, six.text_type):
        value = value.encode('utf-8')
    length = len(value)
    if use_smallest and length <= 255:
        output += _construct(ConstructorBytes.string_small, with_constructor)
        output += _bytes(length)
        return output + value
    try:
        output += _construct(ConstructorBytes.string_large, with_constructor)
        output += _bytes(length, length=4)
        return output + value
    except OverflowError:
        raise ValueError("String value too long to encode.")


def encode_symbol(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Union[bytes, str], bool, bool) -> bytes
    """
    <encoding name="sym8" code="0xa3" category="variable" width="1" label="up to 2^8 - 1 seven bit ASCII characters representing a symbolic value"/>
    <encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>
    """
    if isinstance(value, six.text_type):
        value = value.encode('utf-8')
    length = len(value)
    if use_smallest and length <= 255:
        output += _construct(ConstructorBytes.symbol_small, with_constructor)
        output += _bytes(length)
        return output + value
    try:
        output += _construct(ConstructorBytes.symbol_large, with_constructor)
        output += _bytes(length, length=4)
        return output + value
    except OverflowError:
        raise ValueError("Symbol value too long to encode.")


def encode_list(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Iterable[Any], bool, bool) -> bytes
    """
    <encoding name="list0" code="0x45" category="fixed" width="0" label="the empty list (i.e. the list with no elements)"/>
    <encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>
    <encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>
    """
    count = len(value)
    if use_smallest and count == 0:
        return output + ConstructorBytes.list_0
    encoded_size = 0
    encoded_values = []
    for item in value:
        encoded_values.append(encode_value(b"", item, with_constructor=True))
        encoded_size += len(encoded_values[-1])
    if use_smallest and count <= 255 and encoded_size < 255:
        output += _construct(ConstructorBytes.list_small, with_constructor)
        output += _bytes(encoded_size + 1)
        output += _bytes(count)
    else:
        try:
            output += _construct(ConstructorBytes.list_large, with_constructor)
            output += _bytes(encoded_size + 4, length=4)
            output += _bytes(count, length=4)
        except OverflowError:
            raise ValueError("List is too large or too long to be encoded.")
    return output + b"".join(encoded_values)


def encode_map(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Union[Dict[Any, Any], Iterable[Tuple[Any, Any]]], bool, bool) -> bytes
    """
    <encoding name="map8" code="0xc1" category="compound" width="1" label="up to 2^8 - 1 octets of encoded map data"/>
    <encoding name="map32" code="0xd1" category="compound" width="4" label="up to 2^32 - 1 octets of encoded map data"/>
    """
    count = len(value) * 2
    encoded_size = 0
    encoded_values = []
    try:
        items = value.items()
    except AttributeError:
        items = value
    for key, value in items:
        encoded_values.append(encode_value(b"", key, with_constructor=True))
        encoded_size += len(encoded_values[-1])
        encoded_values.append(encode_value(b"", value, with_constructor=True))
        encoded_size += len(encoded_values[-1])
    if use_smallest and count <= 255 and encoded_size < 255:
        output += _construct(ConstructorBytes.map_small, with_constructor)
        output += _bytes(encoded_size + 1)
        output += _bytes(count)
    else:
        try:
            output += _construct(ConstructorBytes.map_large, with_constructor)
            output += _bytes(encoded_size + 4, length=4)
            output += _bytes(count, length=4)
        except OverflowError:
            raise ValueError("Map is too large or too long to be encoded.")
    return output + b"".join(encoded_values)


def _check_element_type(item, element_type):
    if not element_type:
        try:
            return item['TYPE']
        except (KeyError, TypeError):
            return type(item)
    try:
        if item['TYPE'] != element_type:
            raise TypeError("All elements in an array must be the same type.")
    except (KeyError, TypeError):
        if type(item) != element_type:
            raise TypeError("All elements in an array must be the same type.")
    return element_type
    

def encode_array(output, value, with_constructor=True, use_smallest=True):
    # type: (bytes, Iterable[Any], bool, bool) -> bytes
    """
    <encoding name="map8" code="0xE0" category="compound" width="1" label="up to 2^8 - 1 octets of encoded map data"/>
    <encoding name="map32" code="0xF0" category="compound" width="4" label="up to 2^32 - 1 octets of encoded map data"/>
    """
    count = len(value)
    encoded_size = 0
    encoded_values = []
    first_item = True
    element_type = None
    for item in value:
        element_type = _check_element_type(item, element_type)
        encoded_values.append(encode_value(b"", item, with_constructor=first_item, use_smallest=False))
        encoded_size += len(encoded_values[-1])
        first_item = False
        if item is None:
            encoded_size -= 1
            break
    if use_smallest and count <= 255 and encoded_size < 255:
        output += _construct(ConstructorBytes.array_small, with_constructor)
        output += _bytes(encoded_size + 1)
        output += _bytes(count)
    else:
        try:
            output += _construct(ConstructorBytes.array_large, with_constructor)
            output += _bytes(encoded_size + 4, length=4)
            output += _bytes(count, length=4)
        except OverflowError:
            raise ValueError("Array is too large or too long to be encoded.")
    return output + b"".join(encoded_values)


def encode_described(output, value, with_constructor=True, **kwargs):
    # type: (bytes, Tuple(Any, Any), bool, Any) -> bytes
    """
    """
    output += ConstructorBytes.descriptor
    output = encode_value(output, value[0])
    output = encode_value(output, value[1])
    return output


_ENCODE_MAP = {
    AMQPTypes.null: encode_null,
    AMQPTypes.boolean: encode_boolean,
    AMQPTypes.ubyte: encode_ubyte,
    AMQPTypes.byte: encode_byte,
    AMQPTypes.ushort: encode_ushort,
    AMQPTypes.short: encode_short,
    AMQPTypes.uint: encode_uint,
    AMQPTypes.int: encode_int,
    AMQPTypes.ulong: encode_ulong,
    AMQPTypes.long: encode_long,
    AMQPTypes.float: encode_float,
    AMQPTypes.double: encode_double,
    AMQPTypes.timestamp: encode_timestamp,
    AMQPTypes.uuid: encode_uuid,
    AMQPTypes.binary: encode_binary,
    AMQPTypes.string: encode_string,
    AMQPTypes.symbol: encode_symbol,
    AMQPTypes.list: encode_list,
    AMQPTypes.map: encode_map,
    AMQPTypes.array: encode_array,
    AMQPTypes.described: encode_described,
}


def encode_value(output, value, **kwargs):
    # type: (bytes, Any, Any) -> bytes
    try:
        output = _ENCODE_MAP[value[TYPE]](output, value[VALUE], **kwargs)
    except (KeyError, TypeError):
        if value is None:
            output = encode_null(output, **kwargs)
        elif isinstance(value, bool):
            output = encode_boolean(output, value, **kwargs)
        elif isinstance(value, six.string_types):
            output = encode_string(output, value, **kwargs)
        elif isinstance(value, uuid.UUID):
            output = encode_uuid(output, value, **kwargs)
        elif isinstance(value, bytearray):
            output = encode_binary(output, value, **kwargs)
        elif isinstance(value, float):
            output = encode_double(output, value, **kwargs)
        elif isinstance(value, six.integer_types):
            output = encode_int(output, value, **kwargs)
        elif isinstance(value, datetime):
            output = encode_timestamp(output, value, **kwargs)
        elif isinstance(value, list):
            output = encode_list(output, value, **kwargs)
        elif isinstance(value, tuple):
            output = encode_described(output, value, **kwargs)
        elif isinstance(value, dict):
            output = encode_map(output, value, **kwargs)
        else:
            raise TypeError("Unable to encode unknown value: {}".format(value))
    return output