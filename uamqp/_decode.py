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


_CONSTUCTOR_MAP = {
    ConstructorBytes.null: None,
    ConstructorBytes.bool_true: True,
    ConstructorBytes.bool_false: False,
    ConstructorBytes.uint_0: 0,
    ConstructorBytes.list_0: [],
    ConstructorBytes.ulong_0: 0,
}

COMPOSITES = {
    0x00000023: 'received',
    0x00000024: 'accepted',
    0x00000025: 'rejected',
    0x00000026: 'released',
    0x00000027: 'modified',
}



def decode_boolean(buffer):
    # type: (Decoder, IO) -> None
    return buffer.read(1) == b'\x01'


def decode_ubyte(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>B', buffer.read(1))[0]


def decode_ushort(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>H', buffer.read(2))[0]


def decode_uint_small(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>B', buffer.read(1))[0]


def decode_uint_large(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>I', buffer.read(4))[0]


def decode_ulong_small(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>B', buffer.read(1))[0]


def decode_ulong_large(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>Q', buffer.read(8))[0]


def decode_byte(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>b', buffer.read(1))[0]


def decode_short(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>h', buffer.read(2))[0]


def decode_int_small(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>b', buffer.read(1))[0]


def decode_int_large(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>i', buffer.read(4))[0]


def decode_long_small(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>b', buffer.read(1))[0]


def decode_long_large(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>q', buffer.read(8))[0]


def decode_float(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>f', buffer.read(4))[0]


def decode_double(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>d', buffer.read(8))[0]


def decode_timestamp(buffer):
    # type: (Decoder, IO) -> None
    return struct.unpack('>q', buffer.read(8))[0]


def decode_uuid(buffer):
    # type: (Decoder, IO) -> None
    return uuid.UUID(bytes=buffer.read(16))


def decode_binary_small(buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    return buffer.read(length) or None


def decode_binary_large(buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    return buffer.read(length) or None


def decode_string_small(buffer):  # TODO: Optional decode strings
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    return buffer.read(length).decode('utf-8') or None


def decode_string_large(buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    return buffer.read(length).decode('utf-8') or None


def decode_symbol_small(buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    return buffer.read(length) or None


def decode_symbol_large(buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    return buffer.read(length) or None


def decode_list_small(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    return [decode_value(buffer) for _ in range(count)]


def decode_list_large(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    return [decode_value(buffer) for _ in range(count)]


def decode_map_small(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    return {decode_value(buffer): decode_value(buffer) for _ in range(0, count, 2)}


def decode_map_large(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    return {decode_value(buffer): decode_value(buffer) for _ in range(0, count, 2)}


def decode_array_small(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    subconstructor = buffer.read(1)
    try:
        empty_value = _CONSTUCTOR_MAP[subconstructor]
        return [empty_value] * count
    except KeyError:
        fixed_value = _DECODE_MAP[subconstructor]
        return [fixed_value(buffer) for _ in range(count)]


def decode_array_large(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    subconstructor = buffer.read(1)
    try:
        empty_value = _CONSTUCTOR_MAP[subconstructor]
        return [empty_value] * count
    except KeyError:
        fixed_value = _DECODE_MAP[subconstructor]
        return [fixed_value(buffer) for _ in range(count)]


def decode_described(buffer):
    # type: (Decoder, IO) -> None
    buffer.read(1)  # descriptor constructor will always be ulong
    descriptor = struct.unpack('>B', buffer.read(1))[0]
    value = decode_value(buffer)
    try:
        composite_type = COMPOSITES[descriptor]
        return {composite_type: value}
    except KeyError:
        return value


def decode_value(buffer):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    constructor = buffer.read(1)
    if constructor == ConstructorBytes.null:
        return None
    try:
        return _DECODE_MAP[constructor](buffer)
    except KeyError:
        return _CONSTUCTOR_MAP[constructor]


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
    while True:
        if buffer.read(2):
            descriptor = struct.unpack('>B', buffer.read(1))[0]
            value = decode_value(buffer)
            if descriptor == 0x00000070:
                message["header"] = value
            elif descriptor == 0x00000071:
                message["delivery_annotations"] = value
            elif descriptor == 0x00000072:
                message["message_annotations"] = value
            elif descriptor == 0x00000073:
                message["properties"] = value
            elif descriptor == 0x00000074:
                message["application_properties"] = value
            elif descriptor == 0x00000075:
                try:
                    message["data"].append(value)
                except KeyError:
                    message["data"] = [value]
            elif descriptor == 0x00000076:
                message["sequence"] = value
            elif descriptor == 0x00000077:
                message["value"] = value
            elif descriptor == 0x00000078:
                message["footer"] = value
        else:
            break  # Finished stream
    return message


def decode_frame(data):
    buffer = BytesIO(data[2:])  # First byte is always described type constructor
    frame_type = struct.unpack('>B', buffer.read(1))[0]
    buffer.read(2)  # Discard list constructor and size
    fields_count = struct.unpack('>B', buffer.read(1))[0]
    fields = [decode_value(buffer) for _ in range(fields_count)]
    if frame_type == 0x00000014:
        fields.append(decode_payload(buffer))
    return frame_type, fields


_DECODE_MAP = {
    ConstructorBytes.bool: decode_boolean,
    ConstructorBytes.ubyte: decode_ubyte,
    ConstructorBytes.ushort: decode_ushort,
    ConstructorBytes.uint_small: decode_uint_small,
    ConstructorBytes.uint_large: decode_uint_large,
    ConstructorBytes.ulong_small: decode_ulong_small,
    ConstructorBytes.ulong_large: decode_ulong_large,
    ConstructorBytes.byte: decode_byte,
    ConstructorBytes.short: decode_short,
    ConstructorBytes.int_small: decode_int_small,
    ConstructorBytes.int_large: decode_int_large,
    ConstructorBytes.long_small: decode_long_small,
    ConstructorBytes.long_large: decode_long_large,
    ConstructorBytes.float: decode_float,
    ConstructorBytes.double: decode_double,
    ConstructorBytes.timestamp: decode_timestamp,
    ConstructorBytes.uuid: decode_uuid,
    ConstructorBytes.binary_small: decode_binary_small,
    ConstructorBytes.binary_large: decode_binary_large,
    ConstructorBytes.string_small: decode_string_small,
    ConstructorBytes.string_large: decode_string_large,
    ConstructorBytes.symbol_small: decode_symbol_small,
    ConstructorBytes.symbol_large: decode_symbol_large,
    ConstructorBytes.list_small: decode_list_small,
    ConstructorBytes.list_large: decode_list_large,
    ConstructorBytes.map_small: decode_map_small,
    ConstructorBytes.map_large: decode_map_large,
    ConstructorBytes.array_small: decode_array_small,
    ConstructorBytes.array_large: decode_array_large,
    ConstructorBytes.descriptor: decode_described,
}
