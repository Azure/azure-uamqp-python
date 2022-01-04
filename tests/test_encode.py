#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import datetime
import uuid

import uamqp._encode as encode
from uamqp.types import AMQPTypes, TYPE, VALUE
from uamqp.message import Message, Header, Properties

import pytest


LARGE_BYTES = bytes(4294967296)


def test_encode_null():
    output = bytearray()
    output.clear()
    encode.encode_null(output)
    assert output == b'\x40'

    output.clear()
    encode.encode_value(output, None)
    assert output == b'\x40'

    output.clear()
    encode.encode_value(output, {"TYPE": "NULL", "VALUE": None})
    assert output == b'\x40'


def test_encode_boolean():
    output = bytearray()
    output.clear()
    encode.encode_boolean(output, True)
    assert output == b"\x56\x01"

    output.clear()
    encode.encode_boolean(output, "foo")
    assert output == b"\x56\x01"

    output.clear()
    encode.encode_boolean(output, True, with_constructor=False)
    assert output == b"\x41"

    output.clear()
    encode.encode_value(output, True)
    assert output == b"\x56\x01"

    output.clear()
    encode.encode_value(output, True, with_constructor=False)
    assert output == b"\x41"

    output.clear()
    encode.encode_value(output, {"TYPE": "BOOL", "VALUE": True})
    assert output == b"\x56\x01"

    output.clear()
    encode.encode_value(output, {"TYPE": "BOOL", "VALUE": True}, with_constructor=False)
    assert output == b"\x41"

    output.clear()
    encode.encode_boolean(output, False)
    assert output == b"\x56\x00"

    output.clear()
    encode.encode_boolean(output, "")
    assert output == b"\x56\x00"

    output.clear()
    encode.encode_boolean(output, False, with_constructor=False)
    assert output == b"\x42"

    output.clear()
    encode.encode_value(output, False)
    assert output == b"\x56\x00"

    output.clear()
    encode.encode_value(output, False, with_constructor=False)
    assert output == b"\x42"

    output.clear()
    encode.encode_value(output, {"TYPE": "BOOL", "VALUE": False})
    assert output == b"\x56\x00"

    output.clear()
    encode.encode_value(output, {"TYPE": "BOOL", "VALUE": False}, with_constructor=False)
    assert output == b"\x42"


def test_encode_ubyte():
    output = bytearray()
    output.clear()
    encode.encode_ubyte(output, 255)
    assert output == b"\x50\xFF"

    output.clear()
    encode.encode_ubyte(output, ord('a'))
    assert output == b"\x50\x61"

    output.clear()
    encode.encode_ubyte(output, -1)
    assert output == b"\x50\x01"

    output.clear()
    encode.encode_ubyte(output, 0, with_constructor=False)
    assert output == b"\x00"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_ubyte(output, 256)

    output.clear()
    encode.encode_value(output, {"TYPE": "UBYTE", "VALUE": ord('a')})
    assert output == b"\x50\x61"

    output.clear()
    encode.encode_value(output, {"TYPE": "UBYTE", "VALUE": ord('a')}, with_constructor=False)
    assert output == b"\x61"


def test_encode_ushort():
    output = bytearray()
    output.clear()
    encode.encode_ushort(output, 0)
    assert output == b"\x60\x00\x00"

    output.clear()
    encode.encode_ushort(output, 16963)
    assert output == b"\x60\x42\x43"

    output.clear()
    encode.encode_ushort(output, 255)
    assert output == b"\x60\x00\xFF"

    output.clear()
    encode.encode_ushort(output, -255)
    assert output == b"\x60\x00\xFF"

    output.clear()
    encode.encode_ushort(output, 65535)
    assert output == b"\x60\xFF\xFF"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_ushort(output, 65536)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.ushort, "VALUE": 0})
    assert output == b"\x60\x00\x00"

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.ushort, "VALUE": 0}, with_constructor=False)
    assert output == b"\x00\x00"


def test_encode_uint():
    output = bytearray()
    output.clear()
    output.clear()
    encode.encode_uint(output, 0)
    assert output == b"\x43"

    output.clear()
    output.clear()
    encode.encode_uint(output, 66)
    assert output == b'\x52\x42'

    output.clear()
    output.clear()
    encode.encode_uint(output, -66)
    assert output == b'\x52\x42'

    output.clear()
    output.clear()
    encode.encode_uint(output, 66, with_constructor=False)
    assert output == b'\x42'

    output.clear()
    output.clear()
    encode.encode_uint(output, 255)
    assert output == b'\x52\xFF'

    output.clear()
    output.clear()
    encode.encode_uint(output, 255, use_smallest=False)
    assert output == b'\x70\x00\x00\x00\xFF'

    output.clear()
    output.clear()
    encode.encode_uint(output, 4294967295)
    assert output == b"\x70\xFF\xFF\xFF\xFF"

    output.clear()
    encode.encode_uint(output, 429496700, with_constructor=False)
    assert output == b"\x19\x99\x99\x7C"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_uint(output, 4294967296)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.uint, "VALUE": 66})
    assert output == b'\x52\x42'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.uint, "VALUE": 66}, with_constructor=False, use_smallest=False)
    assert output == b'\x00\x00\x00\x42'


def test_encode_ulong():
    output = bytearray()
    output.clear()
    encode.encode_ulong(output, 0)
    assert output == b"\x44"

    output.clear()
    encode.encode_ulong(output, 66)
    assert output == b'\x53\x42'

    output.clear()
    encode.encode_ulong(output, -66)
    assert output == b'\x53\x42'

    output.clear()
    encode.encode_ulong(output, 66, with_constructor=False)
    assert output == b'\x42'

    output.clear()
    encode.encode_ulong(output, 255)
    assert output == b'\x53\xFF'

    output.clear()
    encode.encode_ulong(output, 255, use_smallest=False)
    assert output == b'\x80\x00\x00\x00\x00\x00\x00\x00\xFF'

    output.clear()
    encode.encode_ulong(output, 4294967295)
    assert output == b"\x80\x00\x00\x00\x00\xFF\xFF\xFF\xFF"

    output.clear()
    encode.encode_ulong(output, 429496700, with_constructor=False)
    assert output == b"\x00\x00\x00\x00\x19\x99\x99\x7C"

    output.clear()
    encode.encode_ulong(output, 18446744073709551615)
    assert output == b"\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_ulong(output, 18446744073709551616)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.ulong, "VALUE": 66})
    assert output == b'\x53\x42'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.ulong, "VALUE": 66}, with_constructor=False, use_smallest=False)
    assert output == b'\x00\x00\x00\x00\x00\x00\x00\x42'


def test_encode_byte():
    output = bytearray()
    output.clear()
    encode.encode_byte(output, 127)
    assert output == b"\x51\x7F"

    output.clear()
    encode.encode_byte(output, 0)
    assert output == b"\x51\x00"

    output.clear()
    encode.encode_byte(output, -1)
    assert output == b"\x51\xFF"

    output.clear()
    encode.encode_byte(output, -128)
    assert output == b"\x51\x80"

    output.clear()
    encode.encode_byte(output, 0, with_constructor=False)
    assert output == b"\x00"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_byte(output, 128)

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_byte(output, -129)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.byte, "VALUE": 66})
    assert output == b'\x51\x42'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.byte, "VALUE": 66}, with_constructor=False)
    assert output == b'\x42'


def test_encode_short():
    output = bytearray()
    output.clear()
    encode.encode_short(output, 0)
    assert output == b"\x61\x00\x00"

    output.clear()
    encode.encode_short(output, -32768)
    assert output == b"\x61\x80\x00"

    output.clear()
    encode.encode_short(output, 32767)
    assert output == b"\x61\x7F\xFF"

    output.clear()
    encode.encode_short(output, 255, with_constructor=False)
    assert output == b"\x00\xFF"

    output.clear()
    encode.encode_short(output, -255)
    assert output == b"\x61\xFF\x01"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_short(output, 32768)

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_short(output, -32769)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.short, "VALUE": 255})
    assert output == b'\x61\x00\xFF'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.short, "VALUE": 255}, with_constructor=False, use_smallest=False)
    assert output == b'\x00\xFF'


def test_encode_int():
    output = bytearray()
    output.clear()
    encode.encode_int(output, 0)
    assert output == b"\x54\x00"

    output.clear()
    encode.encode_int(output, 66)
    assert output == b'\x54\x42'

    output.clear()
    encode.encode_int(output, -66)
    assert output == b'\x54\xBE'

    output.clear()
    encode.encode_int(output, 66, with_constructor=False)
    assert output == b'\x42'

    output.clear()
    encode.encode_int(output, 127)
    assert output == b'\x54\x7F'

    output.clear()
    encode.encode_int(output, -128)
    assert output == b'\x54\x80'

    output.clear()
    encode.encode_int(output, 127, use_smallest=False)
    assert output == b'\x71\x00\x00\x00\x7F'

    output.clear()
    encode.encode_int(output, -1, with_constructor=False, use_smallest=False)
    assert output == b'\xFF\xFF\xFF\xFF'

    output.clear()
    encode.encode_int(output, 2147483647)
    assert output == b"\x71\x7F\xFF\xFF\xFF"

    output.clear()
    encode.encode_int(output, -2147483648, with_constructor=False)
    assert output == b"\x80\x00\x00\x00"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_int(output, 2147483648)

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_int(output, -2147483649)

    output.clear()
    encode.encode_value(output, 66)
    assert output == b'\x54\x42'

    output.clear()
    encode.encode_value(output, 127, with_constructor=False, use_smallest=False)
    assert output == b'\x00\x00\x00\x7F'

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.int, "VALUE": 127})
    assert output == b'\x54\x7F'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.int, "VALUE": 127}, with_constructor=False, use_smallest=False)
    assert output == b'\x00\x00\x00\x7F'


def test_encode_long():
    output = bytearray()
    output.clear()
    encode.encode_long(output, 0)
    assert output == b"\x55\x00"

    output.clear()
    encode.encode_long(output, 66)
    assert output == b'\x55\x42'

    output.clear()
    encode.encode_long(output, -66)
    assert output == b'\x55\xBE'

    output.clear()
    encode.encode_long(output, 66, with_constructor=False)
    assert output == b'\x42'

    output.clear()
    encode.encode_long(output, 127)
    assert output == b'\x55\x7F'

    output.clear()
    encode.encode_long(output, -128)
    assert output == b'\x55\x80'

    output.clear()
    encode.encode_long(output, 127, use_smallest=False)
    assert output == b'\x81\x00\x00\x00\x00\x00\x00\x00\x7F'

    output.clear()
    encode.encode_long(output, 9223372036854775807)
    assert output == b"\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    output.clear()
    encode.encode_long(output, 429496700, with_constructor=False)
    assert output == b"\x00\x00\x00\x00\x19\x99\x99\x7C"

    output.clear()
    encode.encode_long(output, -9223372036854775808)
    assert output == b"\x81\x80\x00\x00\x00\x00\x00\x00\x00"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_long(output, 9223372036854775808)

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_long(output, -9223372036854775809)

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.long, "VALUE": 127})
    assert output == b'\x55\x7F'

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.long, "VALUE": 127}, with_constructor=False, use_smallest=False)
    assert output == b'\x00\x00\x00\x00\x00\x00\x00\x7F'


def test_encode_float():
    output = bytearray()
    output.clear()
    encode.encode_float(output, -1.0)
    assert output == b"\x72\xBF\x80\x00\x00"

    output.clear()
    encode.encode_float(output, 42.0)
    assert output == b"\x72\x42\x28\x00\x00"

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.float, "VALUE": 42.0})
    assert output == b"\x72\x42\x28\x00\x00"

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.float, "VALUE": 42.0}, with_constructor=False, use_smallest=False)
    assert output == b"\x42\x28\x00\x00"


def test_encode_double():
    output = bytearray()
    output.clear()
    encode.encode_double(output, -1.0)
    assert output == b"\x82\xBF\xF0\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_double(output, 42.0)
    assert output == b"\x82\x40\x45\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_value(output, 42.0)
    assert output == b"\x82\x40\x45\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_value(output, 42.0, with_constructor=False, use_smallest=False)
    assert output == b"\x40\x45\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_value(output, {"TYPE": AMQPTypes.double, "VALUE": 42.0})
    assert output == b"\x82\x40\x45\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_value(
        output, {"TYPE": AMQPTypes.double, "VALUE": 42.0}, with_constructor=False, use_smallest=False)
    assert output == b"\x40\x45\x00\x00\x00\x00\x00\x00"


def test_encode_timestamp():
    output = bytearray()
    output.clear()
    encode.encode_timestamp(output, -9223372036854775807 - 1)
    assert output == b"\x83\x80\x00\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_timestamp(output, 0)
    assert output == b"\x83\x00\x00\x00\x00\x00\x00\x00\x00"

    output.clear()
    encode.encode_timestamp(output, 9223372036854775807)
    assert output == b"\x83\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    output.clear()
    encode.encode_timestamp(output, datetime.datetime.min)
    assert output == b"\x83\xFF\xFF\xC7\x7C\xED\xD3\x28\x00"

    output.clear()
    encode.encode_timestamp(output, datetime.datetime.max)
    assert output == b"\x83\x00\x00\xE6\x77\xD2\x1F\xDC\x00"


def test_encode_uuid():
    output = bytearray()
    output.clear()
    encode.encode_uuid(output, '00000000-0000-0000-0000-000000000000')
    assert output == b"\x98\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    id = uuid.UUID('37f9db00-fbb7-11e7-85ee-ecb1d755839a')
    output.clear()
    encode.encode_uuid(output, id)
    assert output == b"\x98\x37\xF9\xDB\x00\xFB\xB7\x11\xE7\x85\xEE\xEC\xB1\xD7\x55\x83\x9A"

    output.clear()
    encode.encode_uuid(output, id, with_constructor=False)
    assert output == b"\x37\xF9\xDB\x00\xFB\xB7\x11\xE7\x85\xEE\xEC\xB1\xD7\x55\x83\x9A"

    output.clear()
    encode.encode_uuid(output, b"\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4A\x4B\x4C\x4D\x4E\x4F")
    assert output == b"\x98\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4A\x4B\x4C\x4D\x4E\x4F"


def test_encode_binary():
    output = bytearray()
    output.clear()
    encode.encode_binary(output, bytes(b''))
    assert output == b"\xA0\x00"

    output.clear()
    encode.encode_binary(output, bytes(b"Test"))
    assert output == b"\xA0\x04Test"
    assert output == b"\xA0\x04\x54\x65\x73\x74"

    output.clear()
    encode.encode_binary(output, bytes(100))
    assert output == b"\xA0\x64" + bytes(100)

    output.clear()
    encode.encode_binary(output, bytes(255))
    assert output == b"\xA0\xFF" + bytes(255)

    output.clear()
    encode.encode_binary(output, bytes(255), use_smallest=False)
    assert output == b"\xB0\x00\x00\x00\xFF" + bytes(255)

    output.clear()
    encode.encode_binary(output, bytes(255), with_constructor=False)
    assert output == b"\xFF" + bytes(255)

    output.clear()
    encode.encode_binary(output, bytes(256))
    assert output == b"\xB0\x00\x00\x01\x00" + bytes(256)

    output.clear()
    encode.encode_binary(output, bytearray([50]))
    assert output == b"\xA0\x01\x32"

    output.clear()
    encode.encode_binary(output, bytearray(b"Test"))
    assert output == b"\xA0\x04Test"
    assert output == b"\xA0\x04\x54\x65\x73\x74"

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_string(output, LARGE_BYTES)


def test_encode_string():
    output = bytearray()
    output.clear()
    encode.encode_string(output, "")
    assert output == b"\xA1\x00"

    output.clear()
    encode.encode_string(output, "Test")
    assert output == b"\xA1\x04Test"
    assert output == b"\xA1\x04\x54\x65\x73\x74"

    output.clear()
    encode.encode_string(output, "A" * 100)
    assert output == b"\xA1\x64" + b"A" * 100

    output.clear()
    encode.encode_string(output, "A" * 255)
    assert output == b"\xA1\xFF" + b"A" * 255

    output.clear()
    encode.encode_string(output, "A" * 255, use_smallest=False)
    assert output == b"\xB1\x00\x00\x00\xFF" + b"A" * 255

    output.clear()
    encode.encode_string(output, "A" * 255, with_constructor=False)
    assert output == b"\xFF" + b"A" * 255

    output.clear()
    encode.encode_string(output, "A" * 256)
    assert output == b"\xB1\x00\x00\x01\x00" + b"A" * 256

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_string(output, LARGE_BYTES)


def test_encode_symbol():
    output = bytearray()
    output.clear()
    encode.encode_symbol(output, "")
    assert output == b"\xA3\x00"

    output.clear()
    encode.encode_symbol(output, "")
    assert output == b"\xA3\x00"

    output.clear()
    encode.encode_symbol(output, "Test")
    assert output == b"\xA3\x04Test"
    assert output == b"\xA3\x04\x54\x65\x73\x74"

    output.clear()
    encode.encode_symbol(output, "A" * 100)
    assert output == b"\xA3\x64" + b"A" * 100

    output.clear()
    encode.encode_symbol(output, "A" * 255)
    assert output == b"\xA3\xFF" + b"A" * 255

    output.clear()
    encode.encode_symbol(output, "A" * 255, use_smallest=False)
    assert output == b"\xB3\x00\x00\x00\xFF" + b"A" * 255

    output.clear()
    encode.encode_symbol(output, "A" * 255, with_constructor=False)
    assert output == b"\xFF" + b"A" * 255

    output.clear()
    encode.encode_symbol(output, "A" * 256)
    assert output == b"\xB3\x00\x00\x01\x00" + b"A" * 256

    output.clear()
    with pytest.raises(ValueError):
        encode.encode_symbol(output, LARGE_BYTES)


def test_encode_list():
    output = bytearray()
    output.clear()
    encode.encode_list(output, [])
    assert output == b'\x45'
    
    output.clear()
    encode.encode_list(output, [1, 2, 3, 4])
    assert output == b"\xC0\x09\x04\x54\x01\x54\x02\x54\x03\x54\x04"

    output.clear()
    encode.encode_list(output, [None])
    assert output == b"\xC0\x02\x01\x40"

    output.clear()
    encode.encode_list(output, [None, None])
    assert output == b"\xC0\x03\x02\x40\x40"

    output.clear()
    encode.encode_list(output, [None for i in range(254)])
    assert output == b"\xC0\xFF\xFE" + b"\x40" * 254

    output.clear()
    encode.encode_list(output, [bytearray(252)])
    assert output == b"\xC0\xFF\x01\xA0\xFC" + bytes(252)

    output.clear()
    encode.encode_list(output, [bytearray(253)])
    assert output == b"\xD0\x00\x00\x01\x03\x00\x00\x00\x01\xA0\xFD" + bytes(253)

    output.clear()
    encode.encode_list(output, [None for i in range(255)])
    assert output == b"\xD0\x00\x00\x01\x03\x00\x00\x00\xFF" + b"\x40" * 255

    output.clear()
    encode.encode_list(output, [b"a"] * 1024 * 256)
    assert output == b"\xD0\x00\x0C\x00\x04\x00\x04\x00\x00" + b"\xA0\x01a" * 1024 * 256

    output.clear()
    encode.encode_list(output, [b"xyz~!@123"] * 128)
    assert output == b"\xD0\x00\x00\x05\x84\x00\x00\x00\x80" + b"\xA0\txyz~!@123" * 128

    output.clear()
    encode.encode_list(output, [bytearray([66]), None])
    assert output == b"\xC0\x05\x02\xA0\x01\x42\x40"

    output.clear()
    encode.encode_list(
        output, [{"TYPE": "BINARY", "VALUE": b"\x42"}, {"TYPE": "NULL", "VALUE": None}])
    assert output == b"\xC0\x05\x02\xA0\x01\x42\x40"

    output.clear()
    encode.encode_value(output, {"TYPE": "LIST", "VALUE": []})
    assert output == b'\x45'

    output.clear()
    encode.encode_value(
        output, {"TYPE": "LIST", "VALUE": [None]}, with_constructor=False, use_smallest=False)
    assert output == b"\x00\x00\x00\x05\x00\x00\x00\x01\x40"


def test_encode_map():
    output = bytearray()
    output.clear()
    encode.encode_map(output, {})
    assert output == b"\xC1\x01\x00"

    output.clear()
    encode.encode_map(output, {None: None})
    assert output == b"\xC1\x03\x02\x40\x40"

    output.clear()
    encode.encode_value(output, {"TYPE": "MAP", "VALUE": {None: None}})
    assert output == b"\xC1\x03\x02\x40\x40"

    output.clear()
    encode.encode_value(
        output, {"TYPE": "MAP", "VALUE": {None: None}}, with_constructor=False, use_smallest=False)
    assert output == b"\x00\x00\x00\x06\x00\x00\x00\x02\x40\x40"

    output.clear()
    encode.encode_map(
        output, [({"TYPE": "UINT", "VALUE": 66}, {"TYPE": "UINT", "VALUE": 67})])
    assert output == b"\xC1\x05\x02\x52\x42\x52\x43"

    input = [({"TYPE": "UINT", "VALUE": i}, None) for i in range(85)]
    output.clear()
    encode.encode_map(output, input)
    expected = b"\xC1\xFF\xAA\x43\x40"
    for i in range(1, 85):
        expected += b"\x52"
        expected += i.to_bytes(1, 'big')
        expected += b"\x40"
    assert expected == output

    input = [({"TYPE": "UINT", "VALUE": i + 1}, None) for i in range(85)]
    output.clear()
    encode.encode_map(output, input)
    expected = b"\xD1\x00\x00\x01\x03\x00\x00\x00\xAA"
    for i in range(85):
        expected += b"\x52"
        expected += (i + 1).to_bytes(1, 'big')
        expected += b"\x40"
    assert expected == output

    input = [({"TYPE": "UINT", "VALUE": i + 1}, None) for i in range(128)]
    output.clear()
    encode.encode_map(output, input)
    expected = b"\xD1\x00\x00\x01\x84\x00\x00\x01\x00"
    for i in range(128):
        expected += b"\x52"
        expected += (i + 1).to_bytes(1, 'big')
        expected += b"\x40"
    assert expected == output


def test_encode_array():
    output = bytearray()
    output.clear()
    encode.encode_array(output, [])
    assert output == b"\xE0\x01\x00"

    output.clear()
    encode.encode_array(output, [None])
    assert output == b"\xE0\x01\x01\x40"

    output.clear()
    encode.encode_array(output, [None, None])
    assert output == b"\xE0\x01\x02\x40"

    input = [{'TYPE': 'LONG', 'VALUE': 9223372036854775807}, {'TYPE': 'LONG', 'VALUE': 9223372036854775807}]
    output.clear()
    encode.encode_array(output, input)
    assert output == b"\xE0\x12\x02\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    output.clear()
    encode.encode_array(output, [[], []])
    assert output == b"\xE0\x12\x02\xD0\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00"

    input = [uuid.UUID('00000000-0000-0000-0000-000000000000') for i in range(8)]
    output.clear()
    encode.encode_array(output, input)
    expected = b"\xE0\x82\x08\x98"
    for i in range(128):
        expected += b"\x00"
    assert output == expected

    output.clear()
    encode.encode_array(output, [None for i in range(254)])
    assert output == b"\xE0\x01\xFE\x40"

    output.clear()
    encode.encode_array(output, [None for i in range(255)])
    assert output == b"\xE0\x01\xFF\x40"

    output.clear()
    encode.encode_array(output, [bytearray(249)])
    assert output == b"\xE0\xFF\x01\xB0\x00\x00\x00\xF9" + bytes(249)

    output.clear()
    encode.encode_array(output, [bytearray(250)])
    assert output == b"\xF0\x00\x00\x01\x03\x00\x00\x00\x01\xB0\x00\x00\x00\xFA" + bytes(250)

    output.clear()
    with pytest.raises(TypeError):
        encode.encode_array(output, [bytearray([10]), 42])


def test_encode_payload():
    data_body_msg1 = Message(data=[b'Abc 123 !@#'])
    output = bytearray()
    encode.encode_payload(output, data_body_msg1)
    assert output == b'\x00Su\xa0\x0bAbc 123 !@#'

    output.clear()
    data_body_msg2 = Message(data=[b'Abc 123 !@#' * 1024])  # 11 * 1024 = 11264 bytes in total
    encode.encode_payload(output, data_body_msg2)
    assert output == b'\x00Su\xb0\x00\x00\x2c\x00' + b'Abc 123 !@#' * 1024  # 0x00002c00 equals to 11264

    output.clear()
    value_body_msg_1 = Message(value='Abc 123 !@#')
    encode.encode_payload(output, value_body_msg_1)
    assert output == b'\x00Sw\xa1\x0bAbc 123 !@#'

    output.clear()
    value_body_msg_2 = Message(value=123.456)
    encode.encode_payload(output, value_body_msg_2)
    assert output == b'\x00Sw\x82@^\xdd/\x1a\x9f\xbew'

    output.clear()
    value_body_msg_3 = Message(value={"key": "value"})
    encode.encode_payload(output, value_body_msg_3)
    assert output == b'\x00Sw\xc1\r\x02\xa1\x03key\xa1\x05value'

    output.clear()
    data_body_with_header_msg1 = Message(
        data=[b'Abc 123 !@#'],
        header=Header(durable=True),
    )
    encode.encode_payload(output, data_body_with_header_msg1)
    assert output == b'\x00\x53\x70\xc0\x07\x05\x56\x01\x40\x40\x40\x40\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'

    output.clear()
    data_body_with_header_msg2 = Message(
        data=[b'Abc 123 !@#'],
        header=Header(durable=True, ttl=1000, delivery_count=1),
    )
    encode.encode_payload(output, data_body_with_header_msg2)
    assert output == b'\x00\x53\x70\xc0\x0c\x05\x56\x01\x40\x70\x00\x00\x03\xe8\x40\x52\x01\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'

    output.clear()
    data_body_with_header_msg3 = Message(
        data=[b'Abc 123 !@#'],
        header=Header(durable=True, priority=1, ttl=1000, first_acquirer=True, delivery_count=1),
    )
    encode.encode_payload(output, data_body_with_header_msg3)
    assert output == b'\x00\x53\x70\xc0\x0e\x05\x56\x01\x50\x01\x70\x00\x00\x03\xe8\x56\x01\x52\x01\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'

    output.clear()
    data_body_with_properties_msg1 = Message(
        data=[b'Abc 123 !@#'],
        properties=Properties(
            message_id=b"1",
            user_id=b'user',
            to=b"t",
            subject=b's',
            reply_to=b"rt",
            correlation_id=b"1",
            content_type=b"ct",
            content_encoding=b"ce",
            absolute_expiry_time=1587603220000,
            creation_time=1587603220000,
            group_id=b"gid",
            group_sequence=100,
            reply_to_group_id=b"rgid"
        )
    )
    encode.encode_payload(output, data_body_with_properties_msg1)
    assert output == b'\x00\x53\x73\xc0\x3e\x0d\xa0\x01\x31\xa0\x04\x75\x73\x65\x72\xa1\x01\x74\xa1\x01\x73\xa1\x02\x72\x74\xa0\x01\x31\xa3\x02\x63\x74\xa3\x02\x63\x65\x83\x00\x00\x01\x71\xa4\x86\xa6\x20\x83\x00\x00\x01\x71\xa4\x86\xa6\x20\xa1\x03\x67\x69\x64\x52\x64\xa1\x04\x72\x67\x69\x64\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'

    output.clear()
    data_body_with_properties_msg2 = Message(
        data=[b'Abc 123 !@#'],
        properties=Properties(
            message_id=b"1",
            content_encoding=b"ce",
            creation_time=1587603220000
        )
    )
    encode.encode_payload(output, data_body_with_properties_msg2)
    assert output == b'\x00\x53\x73\xc0\x1b\x0d\xa0\x01\x31\x40\x40\x40\x40\x40\x40\xa3\x02\x63\x65\x40\x83\x00\x00\x01\x71\xa4\x86\xa6\x20\x40\x40\x40\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'

    output.clear()
    data_body_with_properties_and_header_msg1 = Message(
        data=[b'Abc 123 !@#'],
        header=Header(durable=True, priority=1, ttl=1000, first_acquirer=True, delivery_count=1),
        properties=Properties(
            message_id=b"1",
            user_id=b'user',
            to=b"t",
            subject=b's',
            reply_to=b"rt",
            correlation_id=b"1",
            content_type=b"ct",
            content_encoding=b"ce",
            absolute_expiry_time=1587603220000,
            creation_time=1587603220000,
            group_id=b"gid",
            group_sequence=100,
            reply_to_group_id=b"rgid"
        )
    )
    encode.encode_payload(output, data_body_with_properties_and_header_msg1)
    assert output == b'\x00\x53\x70\xc0\x0e\x05\x56\x01\x50\x01\x70\x00\x00\x03\xe8\x56\x01\x52\x01\x00\x53\x73\xc0\x3e\x0d\xa0\x01\x31\xa0\x04\x75\x73\x65\x72\xa1\x01\x74\xa1\x01\x73\xa1\x02\x72\x74\xa0\x01\x31\xa3\x02\x63\x74\xa3\x02\x63\x65\x83\x00\x00\x01\x71\xa4\x86\xa6\x20\x83\x00\x00\x01\x71\xa4\x86\xa6\x20\xa1\x03\x67\x69\x64\x52\x64\xa1\x04\x72\x67\x69\x64\x00\x53\x75\xa0\x0b\x41\x62\x63\x20\x31\x32\x33\x20\x21\x40\x23'


def test_encode_described():
    described_value = (
        {TYPE: AMQPTypes.ulong, VALUE: 0x0123456789abcdef},
        {TYPE: AMQPTypes.string, VALUE: 'describedstring'}
    )

    output = bytearray()
    encode.encode_described(output, described_value)
    # x00 is the constructor for described value
    # x80 indicates the descriptor is a ulong
    # x01\x23\x45\x67\x89\xab\xcd\xef is the descriptor value
    # xa1 indicates the type for the value being described is a string
    # x0f indicates the length of the string
    assert output == b'\x00\x80\x01\x23\x45\x67\x89\xab\xcd\xef\xa1\x0fdescribedstring'

    described_value = (
        {TYPE: AMQPTypes.symbol, VALUE: 'descriptorsymbol'},
        {TYPE: AMQPTypes.string, VALUE: 'describedstring'}
    )

    output.clear()
    encode.encode_described(output, described_value)
    # same as the above one except that the second byte xa3 indicated  the descriptor is a symbol
    assert output == b'\x00\xa3\x10descriptorsymbol\xa1\x0fdescribedstring'
