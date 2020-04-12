#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
# pylint: disable=redefined-builtin, import-error

import struct
import uuid
from io import BytesIO
import logging
from typing import Iterable, Union, Tuple, Dict  # pylint: disable=unused-import

from .types import ConstructorBytes
from .performatives import (
    HeaderFrame,
    TLSHeaderFrame,
    SASLHeaderFrame)


_LOGGER = logging.getLogger(__name__)
_HEADER_PREFIX = memoryview(b'AMQP')
_COMPOSITES = {
    35: 'received',
    36: 'accepted',
    37: 'rejected',
    38: 'released',
    39: 'modified',
}

# Array for the number of fields in each performative type. We use this because
# lookup will be faster than reading the count.
_FRAME_FIELD_ARRAY = [None] * 70
_FRAME_FIELD_ARRAY[16] = 10
_FRAME_FIELD_ARRAY[17] = 8
_FRAME_FIELD_ARRAY[18] = 14
_FRAME_FIELD_ARRAY[19] = 11
_FRAME_FIELD_ARRAY[20] = 11
_FRAME_FIELD_ARRAY[21] = 6
_FRAME_FIELD_ARRAY[22] = 3
_FRAME_FIELD_ARRAY[23] = 1
_FRAME_FIELD_ARRAY[24] = 1
_FRAME_FIELD_ARRAY[64] = 1
_FRAME_FIELD_ARRAY[65] = 3
_FRAME_FIELD_ARRAY[66] = 1
_FRAME_FIELD_ARRAY[67] = 1
_FRAME_FIELD_ARRAY[68] = 2


c_unsigned_char = struct.Struct('>B')
c_signed_char = struct.Struct('>b')
c_unsigned_short = struct.Struct('>H')
c_signed_short = struct.Struct('>h')
c_unsigned_int = struct.Struct('>I')
c_signed_int = struct.Struct('>i')
c_unsigned_long = struct.Struct('>L')
c_unsigned_long_long = struct.Struct('>Q')
c_signed_long_long = struct.Struct('>q')
c_float = struct.Struct('>f')
c_double = struct.Struct('>d')


def _decode_null(buffer):
    return buffer, None

def _decode_true(buffer):
    return buffer, True

def _decode_false(buffer):
    return buffer, False

def _decode_zero(buffer):
    return buffer, 0

def _decode_empty(buffer):
    return buffer, []

def _decode_boolean(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], buffer[:1] == b'\x01'


def _decode_ubyte(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], buffer[0]


def _decode_ushort(buffer):
    # type: (Decoder, IO) -> None
    return buffer[2:], c_unsigned_short.unpack(buffer[:2])[0]


def _decode_uint_small(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], buffer[0]


def _decode_uint_large(buffer):
    # type: (Decoder, IO) -> None
    return buffer[4:], c_unsigned_int.unpack(buffer[:4])[0]


def _decode_ulong_small(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], buffer[0]


def _decode_ulong_large(buffer):
    # type: (Decoder, IO) -> None
    return buffer[8:], c_unsigned_long_long.unpack(buffer[:8])[0]


def _decode_byte(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], c_signed_char.unpack(buffer[:1])[0]


def _decode_short(buffer):
    # type: (Decoder, IO) -> None
    return buffer[2:], c_signed_short.unpack(buffer[:2])[0]


def _decode_int_small(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], c_signed_char.unpack(buffer[:1])[0]


def _decode_int_large(buffer):
    # type: (Decoder, IO) -> None
    return buffer[4:], c_signed_int.unpack(buffer[:4])[0]


def _decode_long_small(buffer):
    # type: (Decoder, IO) -> None
    return buffer[1:], c_signed_char.unpack(buffer[:1])[0]


def _decode_long_large(buffer):
    # type: (Decoder, IO) -> None
    return buffer[8:], c_signed_long_long.unpack(buffer[:8])[0]


def _decode_float(buffer):
    # type: (Decoder, IO) -> None
    return buffer[4:], c_float.unpack(buffer[:4])[0]


def _decode_double(buffer):
    # type: (Decoder, IO) -> None
    return buffer[8:], c_double.unpack(buffer[:8])[0]


def _decode_timestamp(buffer):
    # type: (Decoder, IO) -> None
    return buffer[8:], c_signed_long_long.unpack(buffer[:8])[0]


def _decode_uuid(buffer):
    # type: (Decoder, IO) -> None
    return buffer[16:], uuid.UUID(bytes=buffer[:16])


def _decode_binary_small(buffer):
    # type: (Decoder, IO) -> None
    length = buffer[0]
    return buffer[1 + length:], buffer[1:1 + length].tobytes() or None


def _decode_binary_large(buffer):
    # type: (Decoder, IO) -> None
    length = c_unsigned_long.unpack(buffer[:4])[0]
    return buffer[4 + length:], buffer[4:4 + length].tobytes() or None


def _decode_string_small(buffer):  # TODO: Optional decode strings
    # type: (Decoder, IO) -> None
    length = buffer[0]
    return buffer[1 + length:], buffer[1:1 + length].tobytes() or None


def _decode_string_large(buffer):
    # type: (Decoder, IO) -> None
    length = c_unsigned_long.unpack(buffer[:4])[0]
    return buffer[4 + length:], buffer[4:4 + length].tobytes() or None


def _decode_symbol_small(buffer):
    # type: (Decoder, IO) -> None
    length = buffer[0]
    return buffer[1 + length:], buffer[1:1 + length].tobytes() or None


def _decode_symbol_large(buffer):
    # type: (Decoder, IO) -> None
    length = c_unsigned_long.unpack(buffer[:4])[0]
    return buffer[4 + length:], buffer[4:4 + length].tobytes() or None


def _decode_list_small(buffer):
    # type: (Decoder, IO) -> None
    count = buffer[1]
    buffer = buffer[2:]
    values = []
    for _ in range(count):
        buffer, value = _DECODE_ARRAY[buffer[0]](buffer[1:])
        values.append(value)
    return buffer, values


def _decode_list_large(buffer):
    # type: (Decoder, IO) -> None
    count = c_unsigned_long.unpack(buffer[4:8])[0]
    buffer = buffer[8:]
    values = []
    for _ in range(count):
        buffer, value = _DECODE_ARRAY[buffer[0]](buffer[1:])
        values.append(value)
    return buffer, values


def _decode_map_small(buffer):
    # type: (Decoder, IO) -> None
    count = buffer[1]
    buffer = buffer[2:]
    values = {}
    for  _ in range(0, count, 2):
        buffer, key = _DECODE_ARRAY[buffer[0]](buffer[1:])
        buffer, value = _DECODE_ARRAY[buffer[0]](buffer[1:])
        values[key] = value
    return buffer, values


def _decode_map_large(buffer):
    # type: (Decoder, IO) -> None
    count = c_unsigned_long.unpack(buffer[4:8])[0]
    buffer = buffer[8:]
    values = {}
    for  _ in range(0, count, 2):
        buffer, key = _DECODE_ARRAY[buffer[0]](buffer[1:])
        buffer, value = _DECODE_ARRAY[buffer[0]](buffer[1:])
        values[key] = value
    return buffer, values


def _decode_array_small(buffer):
    # type: (Decoder, IO) -> None
    count = buffer[1]
    subconstructor = buffer[2]
    buffer = buffer[3:]
    values = []
    for  _ in range(count):
        buffer, value = _DECODE_ARRAY[subconstructor](buffer)
        values.append(value)
    return buffer, values


def _decode_array_large(buffer):
    # type: (Decoder, IO) -> None
    count = c_unsigned_long.unpack(buffer[4:8])[0]
    subconstructor = buffer[8]
    buffer = buffer[9:]
    values = []
    for  _ in range(count):
        buffer, value = _DECODE_ARRAY[subconstructor](buffer)
        values.append(value)
    return buffer, values

def _decode_described(buffer):
    # type: (Decoder, IO) -> None
    buffer, value = _DECODE_ARRAY[buffer[2]](buffer[3:])
    try:
        composite_type = _COMPOSITES[buffer[1]]
        return buffer, {composite_type: value}
    except (KeyError, IndexError):
        return buffer, value


def decode_empty_frame(header):
    # type: (bytes) -> Performative
    if header[0:4] == _HEADER_PREFIX:
        layer = header[4]
        if layer == 0:
            return HeaderFrame(header=header)
        if layer == 2:
            return TLSHeaderFrame(header=header)
        if layer == 3:
            return SASLHeaderFrame(header=header)
        raise ValueError("Received unexpected IO layer: {}".format(layer))
    if header[5] == 0:
        return "EMPTY"
    raise ValueError("Received unrecognized empty frame")


def decode_payload(buffer):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    message = {}
    while buffer:
        descriptor = buffer[2]
        buffer, value = _DECODE_ARRAY[buffer[3]](buffer[4:])
        if descriptor == 112:
            message["header"] = value
        elif descriptor == 113:
            message["delivery_annotations"] = value
        elif descriptor == 114:
            message["message_annotations"] = value
        elif descriptor == 115:
            message["properties"] = value
        elif descriptor == 116:
            message["application_properties"] = value
        elif descriptor == 117:
            try:
                message["data"].append(value)
            except KeyError:
                message["data"] = [value]
        elif descriptor == 118:
            message["sequence"] = value
        elif descriptor == 119:
            message["value"] = value
        elif descriptor == 120:
            message["footer"] = value
    return message


def decode_frame(data):
    # Ignore the first two bytes, they will always be the constructors for
    # described type then ulong.
    frame_type = data[2]
    # Ignore the next 3 bytes, they will always be list constructor, size, and count.
    buffer = data[6:]
    fields = []
    for _ in range(_FRAME_FIELD_ARRAY[frame_type]):
        buffer, field = _DECODE_ARRAY[buffer[0]](buffer[1:])
        fields.append(field)
    if frame_type == 20:
        fields.append(_decode_payload(buffer))
    return frame_type, fields


_DECODE_ARRAY = [None] * 256
_DECODE_ARRAY[64] = _decode_null
_DECODE_ARRAY[86] = _decode_boolean
_DECODE_ARRAY[65] = _decode_true
_DECODE_ARRAY[66] = _decode_false
_DECODE_ARRAY[80] = _decode_ubyte
_DECODE_ARRAY[81] = _decode_byte
_DECODE_ARRAY[96] = _decode_ushort
_DECODE_ARRAY[97] = _decode_short
_DECODE_ARRAY[67] = _decode_zero
_DECODE_ARRAY[82] = _decode_uint_small
_DECODE_ARRAY[84] = _decode_int_small
_DECODE_ARRAY[112] = _decode_uint_large
_DECODE_ARRAY[113] = _decode_int_large
_DECODE_ARRAY[68] = _decode_zero
_DECODE_ARRAY[83] = _decode_ulong_small
_DECODE_ARRAY[85] = _decode_long_small
_DECODE_ARRAY[128] = _decode_ulong_large
_DECODE_ARRAY[129] = _decode_long_large
_DECODE_ARRAY[114] = _decode_float
_DECODE_ARRAY[130] = _decode_double
_DECODE_ARRAY[131] = _decode_timestamp
_DECODE_ARRAY[152] = _decode_uuid
_DECODE_ARRAY[160] = _decode_binary_small
_DECODE_ARRAY[176] = _decode_binary_large
_DECODE_ARRAY[161] = _decode_string_small
_DECODE_ARRAY[177] = _decode_string_large
_DECODE_ARRAY[163] = _decode_symbol_small
_DECODE_ARRAY[179] = _decode_symbol_large
_DECODE_ARRAY[69] = _decode_empty
_DECODE_ARRAY[192] = _decode_list_small
_DECODE_ARRAY[208] = _decode_list_large
_DECODE_ARRAY[193] = _decode_map_small
_DECODE_ARRAY[209] = _decode_map_large
_DECODE_ARRAY[224] = _decode_array_small
_DECODE_ARRAY[240] = _decode_array_large
_DECODE_ARRAY[0] = _decode_described
