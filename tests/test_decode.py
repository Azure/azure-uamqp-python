#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import datetime
import uuid

from uamqp import _decode as decode
from uamqp.amqp_types import AMQPTypes, TYPE, VALUE

import pytest


def decode_value(buffer):
    return decode._DECODE_BY_CONSTRUCTOR[buffer[0]](buffer[1:])

def test_decode_null():
    buffer = memoryview(b"\x40")
    out_buffer, output = decode_value(buffer)
    assert output == None
    assert not out_buffer

    # buffer = memoryview(b"\x40\x40")
    # output = decode_value(buffer, length_bytes=2)
    # assert output == [None, None]


def test_decode_boolean():
    buffer = memoryview(b"\x56\x00")
    out_buffer, output = decode_value(buffer)
    assert output == False
    assert not out_buffer

    buffer = memoryview(b"\x56\x01")
    out_buffer, output = decode_value(buffer)
    assert output == True
    assert not out_buffer

    buffer = memoryview(b"\x41")
    out_buffer, output = decode_value(buffer)
    assert output == True
    assert not out_buffer

    buffer = memoryview(b"\x42")
    out_buffer, output = decode_value(buffer)
    assert output == False
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x56")
    #     decode_value(buffer)

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x56\x02")
    #     decode_value(buffer)


def test_decode_ubyte():
    buffer = memoryview(b"\x50\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x50\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 255
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x50")
    #     decode_value(buffer)


def test_decode_ushort():
    buffer = memoryview(b"\x60\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x60\xFF\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 65535
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x60\x00")
    #     decode_value(buffer)


def test_decode_uint():
    buffer = memoryview(b"\x70\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x70\x42\x43\x44\x45")
    out_buffer, output = decode_value(buffer)
    assert output == 1111704645
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x70\x42\x43")
    #     decode_value(buffer)

    buffer = memoryview(b"\x52\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x52\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 255
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x52")
    #     decode_value(buffer)

    buffer = memoryview(b"\x43")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer


def test_decode_ulong():
    buffer = memoryview(b"\x80\x00\x00\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x80\x42\x43\x44\x45\x46\x47\x48\x49")
    out_buffer, output = decode_value(buffer)
    assert output == 4774735094265366601
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x80\x42\x43\x44\x45\x46\x47")
    #     decode_value(buffer)

    buffer = memoryview(b"\x53\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer

    buffer = memoryview(b"\x53\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 255
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x53")
    #     decode_value(buffer)

    buffer = memoryview(b"\x44")
    out_buffer, output = decode_value(buffer)
    assert output == 0
    assert not out_buffer


def test_decode_byte():
    buffer = memoryview(b"\x51\x80")
    out_buffer, output = decode_value(buffer)
    assert output == -128
    assert not out_buffer

    buffer = memoryview(b"\x51\x7F")
    out_buffer, output = decode_value(buffer)
    assert output == 127
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x51")
    #     decode_value(buffer)


def test_decode_short():
    buffer = memoryview(b"\x61\x80\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -32768
    assert not out_buffer

    buffer = memoryview(b"\x61\x7F\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 32767
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x61\x7F")
    #     decode_value(buffer)


def test_decode_int():
    buffer = memoryview(b"\x71\x80\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -2147483648
    assert not out_buffer

    buffer = memoryview(b"\x71\x7F\xFF\xFF\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 2147483647
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x71\x7F\xFF\xFF")
    #     decode_value(buffer)

    buffer = memoryview(b"\x54\x80")
    out_buffer, output = decode_value(buffer)
    assert output == -128
    assert not out_buffer

    buffer = memoryview(b"\x54\x7F")
    out_buffer, output = decode_value(buffer)
    assert output == 127
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x54")
    #     decode_value(buffer)


def test_decode_long():
    buffer = memoryview(b"\x81\x80\x00\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -9223372036854775808
    assert not out_buffer

    buffer = memoryview(b"\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 9223372036854775807
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF")
    #     decode_value(buffer)

    buffer = memoryview(b"\x55\x80")
    out_buffer, output = decode_value(buffer)
    assert output == -128
    assert not out_buffer

    buffer = memoryview(b"\x55\x7F")
    out_buffer, output = decode_value(buffer)
    assert output == 127
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x55")
    #     decode_value(buffer)


def test_decode_float():
    buffer = memoryview(b"\x72\xBF\x80\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -1.0
    assert not out_buffer

    buffer = memoryview(b"\x72\x42\x28\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 42.0
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x72\x42")
    #     decode_value(buffer)


def test_decode_double():
    buffer = memoryview(b"\x82\x40\x45\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == 42.0
    assert not out_buffer

    buffer = memoryview(b"\x82\xBF\xF0\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -1.0
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x82\x40\x45")
    #     decode_value(buffer)


def test_decode_timestamp():
    buffer = memoryview(b"\x83\x80\x00\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == -9223372036854775808
    assert not out_buffer

    buffer = memoryview(b"\x83\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == 9223372036854775807
    assert not out_buffer

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x83\x7F\xFF\xFF\xFF\xFF\xFF\xFF")
    #     decode_value(buffer)


def test_decode_uuid():
    buffer = memoryview(b"\x98\x01\x02\x03\x04\x05\x06\x07\x08\x11\x12\x13\x14\x15\x16\x17\x18")
    out_buffer, output = decode_value(buffer)
    assert output == uuid.UUID(bytes=b"\x01\x02\x03\x04\x05\x06\x07\x08\x11\x12\x13\x14\x15\x16\x17\x18")
    assert not out_buffer


def test_decode_binary():
    buffer = memoryview(b"\xA0\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xA0\x01\x42")
    out_buffer, output = decode_value(buffer)
    assert output == b"B"
    assert not out_buffer

    buffer = memoryview(b"\xA0\xFF" + b"A" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == b"A" * 255
    assert not out_buffer

    buffer = memoryview(b"\xB0\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xB0\x00\x00\x00\x01\x42")
    out_buffer, output = decode_value(buffer)
    assert output == b"B"
    assert not out_buffer

    buffer = memoryview(b"\xB0\x00\x00\x01\x00" + b"A" * 256)
    out_buffer, output = decode_value(buffer)
    assert output == b"A" * 256
    assert not out_buffer


def test_decode_string():
    buffer = memoryview(b"\xA1\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xA1\x01a")
    out_buffer, output = decode_value(buffer)
    assert output == b"a"
    assert not out_buffer

    buffer = memoryview(b"\xA1\xFF" + b"x" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == b"x" * 255
    assert not out_buffer

    buffer = memoryview(b"\xB1\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xB1\x00\x00\x00\x01a")
    out_buffer, output = decode_value(buffer)
    assert output == b"a"
    assert not out_buffer

    buffer = memoryview(b"\xB0\x00\x00\x00\xFF" + b"x" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == b"x" * 255
    assert not out_buffer

    buffer = memoryview(b"\xB0\x00\x00\x01\x00" + b"x" * 256)
    out_buffer, output = decode_value(buffer)
    assert output == b"x" * 256
    assert not out_buffer

def test_decode_symbol():
    buffer = memoryview(b"\xA3\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xA3\x01a")
    out_buffer, output = decode_value(buffer)
    assert output == b"a"
    assert not out_buffer

    buffer = memoryview(b"\xA3\xFF" + b"s" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == b"s" * 255
    assert not out_buffer

    buffer = memoryview(b"\xB3\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == b""
    assert not out_buffer

    buffer = memoryview(b"\xB3\x00\x00\x00\x01a")
    out_buffer, output = decode_value(buffer)
    assert output == b"a"
    assert not out_buffer

    buffer = memoryview(b"\xB3\x00\x00\x00\xFF" + b"s" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == b"s" * 255
    assert not out_buffer

    buffer = memoryview(b"\xB3\x00\x00\x01\x00" + b"s" * 256)
    out_buffer, output = decode_value(buffer)
    assert output == b"s" * 256
    assert not out_buffer


def test_decode_list():
    buffer = memoryview(b"\x45")
    out_buffer, output = decode_value(buffer)
    assert output == []
    assert not out_buffer

    buffer = memoryview(b"\xC0\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == []
    assert not out_buffer

    buffer = memoryview(b"\xC0\x00\x01\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None]
    assert not out_buffer

    buffer = memoryview(b"\xC0\x02\x02\x40\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None, None]
    assert not out_buffer

    buffer = memoryview(b"\xC0\xFF\xFF" + b"\x40" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 255
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == []
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x00\x01\x00\x00\x00\x01\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None]
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x00\x02\x00\x00\x00\x02\x40\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None, None]
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x00\xFF\x00\x00\x00\xFF" + b"\x40" * 255)
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 255
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x01\x00\x00\x00\x01\x00" + b"\x40" * 256)
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 256
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x0C\x00\x04\x00\x04\x00\x00" + b"\xA0\x01a" * 1024 * 256)
    out_buffer, output = decode_value(buffer)
    assert output == [b"a"] * 1024 * 256
    assert not out_buffer

    buffer = memoryview(b"\xD0\x00\x00\x05\x84\x00\x00\x00\x80" + b"\xA0\txyz~!@123" * 128)
    out_buffer, output = decode_value(buffer)
    assert output == [b"xyz~!@123"] * 128
    assert not out_buffer

def test_decode_map():
    buffer = memoryview(b"\xC1\x01\x00")
    out_buffer, output = decode_value(buffer)
    assert output == {}
    assert not out_buffer

    buffer = memoryview(b"\xC1\x07\x02\xA3\x01k\xA0\x01v")
    out_buffer, output = decode_value(buffer)
    assert output == {b'k': b'v'}
    assert not out_buffer

    buffer = memoryview(b"\xD1\x00\x00\x00\x01\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == {}
    assert not out_buffer

    buffer = memoryview(b"\xD1\x00\x00\x00\x07\x00\x00\x00\x02\xA3\x01k\xA0\x01v")
    out_buffer, output = decode_value(buffer)
    assert output == {b'k': b'v'}
    assert not out_buffer


def test_decode_array():
    buffer = memoryview(b"\xE0\x01\x00")
    out_buffer, output = decode_value(buffer)
    assert output == []
    assert not out_buffer

    buffer = memoryview(b"\xE0\x01\x01\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None]
    assert not out_buffer

    buffer = memoryview(b"\xE0\x01\x02\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None, None]
    assert not out_buffer

    buffer = memoryview(b"\xE0\x11\x02\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    out_buffer, output = decode_value(buffer)
    assert output == [9223372036854775807, 9223372036854775807]
    assert not out_buffer

    buffer = memoryview(b"\xE0\x01\xFF\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 255
    assert not out_buffer

    buffer = memoryview(b"\xF0\x00\x00\x00\x00\x00\x00\x00\x00")
    out_buffer, output = decode_value(buffer)
    assert output == []
    assert not out_buffer

    buffer = memoryview(b"\xF0\x00\x00\x00\x01\x00\x00\x00\x01\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None]
    assert not out_buffer

    buffer = memoryview(b"\xF0\x00\x00\x00\x01\x00\x00\x00\x02\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None, None]
    assert not out_buffer

    buffer = memoryview(b"\xF0\x00\x00\x00\x01\x00\x00\x00\xFF\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 255
    assert not out_buffer

    buffer = memoryview(b"\xF0\x00\x00\x00\x01\x00\x00\x01\x00\x40")
    out_buffer, output = decode_value(buffer)
    assert output == [None] * 256
    assert not out_buffer


def test_decode_described():
    buffer = memoryview(b'\x00\x80\x01\x23\x45\x67\x89\xab\xcd\xef\xa1\x0fdescribedstring')
    out_buffer, output = decode_value(buffer)
    assert output == b'describedstring'

    buffer = memoryview(b'\x00\xa3\x10descriptorsymbol\xa1\x0fdescribedstring')
    out_buffer, output = decode_value(buffer)
    assert output == b'describedstring'
