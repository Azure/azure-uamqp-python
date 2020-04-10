#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
# pylint: disable=redefined-builtin

import struct
import uuid
from io import BytesIO
import logging
from typing import Iterable, Union, Tuple, Dict  # pylint: disable=unused-import

try:
    from uamqp_encoder.c_uamqp import c_decode_frame
except ImportError:
    c_decode_frame = None

from uamqp.types import ConstructorBytes
from uamqp.error import AMQPError
from uamqp.performatives import (
    HeaderFrame,
    TLSHeaderFrame,
    SASLHeaderFrame,
    OpenFrame,
    BeginFrame,
    AttachFrame,
    FlowFrame,
    TransferFrame,
    DispositionFrame,
    DetachFrame,
    EndFrame,
    CloseFrame,
    SASLMechanism,
    SASLInit,
    SASLChallenge,
    SASLResponse,
    SASLOutcome)
from uamqp.endpoints import Source, Target
from uamqp.message import Header, Properties
from uamqp.outcomes import (
    Received,
    Accepted,
    Rejected,
    Released,
    Modified,
)


_LOGGER = logging.getLogger(__name__)
_MESSAGE_PERFORMATIVES = [Header, Properties]
_HEADER_PREFIX = memoryview(b'AMQP')


_CONSTUCTOR_MAP = {
    ConstructorBytes.null: None,
    ConstructorBytes.bool_true: True,
    ConstructorBytes.bool_false: False,
    ConstructorBytes.uint_0: 0,
    ConstructorBytes.list_0: [],
    ConstructorBytes.ulong_0: 0,
}


PERFORMATIVES = {
    0x00000010: OpenFrame,
    0x00000011: BeginFrame,
    0x00000012: AttachFrame,
    0x00000013: FlowFrame,
    0x00000014: TransferFrame,
    0x00000015: DispositionFrame,
    0x00000016: DetachFrame,
    0x00000017: EndFrame,
    0x00000018: CloseFrame,
    0x00000040: SASLMechanism,
    0x00000041: SASLInit,
    0x00000042: SASLChallenge,
    0x00000043: SASLResponse,
    0x00000044: SASLOutcome
}

COMPOSITES = {
    0x00000023: Received,
    0x00000024: Accepted,
    0x00000025: Rejected,
    0x00000026: Released,
    0x00000027: Modified,
    0x00000028: Source,
    0x00000029: Target,
    0x0000001d: AMQPError,
}


MESSAGE_SECTIONS = {
    0x00000070: "header",
    0x00000071: "delivery_annotations",
    0x00000072: "message_annotations",
    0x00000073: "properties",
    0x00000074: "application_properties",
    0x00000075: "data",
    0x00000076: "sequence",
    0x00000077: "value",
    0x00000078: "footer"
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
    return struct.unpack('>Q',  buffer.read(8))[0]


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


def decode_list_values(buffer, count):
    decoded_values = []
    for _ in range(count):
        constructor = buffer.read(1)
        try:
            value = _CONSTUCTOR_MAP[constructor]
            decoded_values.append(value)
        except KeyError:
            type_decoder = _DECODE_MAP[constructor]
            decoded_values.append(type_decoder(buffer))
    return decoded_values


def decode_list_small(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    return decode_list_values(buffer, count)


def decode_list_large(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    return decode_list_values(buffer, count)


def decode_map_small(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    values = decode_list_values(buffer, count)
    return dict([(values[i], values[i+1]) for i in range(0, count, 2)])


def decode_map_large(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    values = decode_list_values(buffer, count)
    return dict([(values[i], values[i+1]) for i in range(0, count, 2)])


def decode_array_values(buffer, count):
    decoded_values = []
    constructor = buffer.read(1)
    try:
        value = _CONSTUCTOR_MAP[constructor]
        return [value] * count
    except KeyError:
        type_decoder = _DECODE_MAP[constructor]
        for _ in range(count):
            decoded_values.append(type_decoder(buffer))
    return decoded_values


def decode_array_small(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(1)  # Discard size
    count = struct.unpack('>B', buffer.read(1))[0]
    return decode_array_values(buffer, count)


def decode_array_large(buffer):
    # type: (Decoder, IO) -> None
    _ = buffer.read(4)  # Discard size
    count = struct.unpack('>L', buffer.read(4))[0]
    return decode_array_values(buffer, count)


def decode_described(buffer):
    # type: (Decoder, IO) -> None
    descriptor = decode_value(buffer)
    value = decode_value(buffer)
    try:
        composite_type = COMPOSITES[descriptor]
        return composite_type(*value)
    except KeyError:
        return value


def decode_message_section(buffer, message):
    # type: (Decoder, IO) -> None
    descriptor = decode_value(buffer)
    section_type = MESSAGE_SECTIONS[descriptor]
    value = decode_value(buffer)
    if section_type == 'data':
        try:
            message[section_type].append(value)
        except KeyError:
            message[section_type] = [value]
    else:
        message[section_type] = value


def decode_value(buffer):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    constructor = buffer.read(1)
    try:
        value = _CONSTUCTOR_MAP[constructor]
    except KeyError:
        value = _DECODE_MAP[constructor](buffer)
    return value


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
    elif header[5] == 0:
        return "EMPTY"
    raise ValueError("Received unrecognized empty frame")


def decode_payload(buffer):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    message = {}
    while True:
        constructor = buffer.read(1)
        if constructor:
            decode_message_section(buffer, message)
        else:
            break  # Finished stream
    return message

def py_decode_frame(data):
    buffer = BytesIO(data)
    _ = buffer.read(1)  # First byte is always described type constructor
    frame_type = decode_value(buffer)
    fields = decode_value(buffer)
    return frame_type, fields, buffer

def decode_frame(size, data):
    # type: (int, memoryview) -> namedtuple
    #_LOGGER.debug("Incoming bytes: %r", data.tobytes())
    if c_decode_frame:
        frame_type, fields, payload = c_decode_frame(size, data.tobytes())
    else:
        frame_type, fields, payload = py_decode_frame(data)
    
    frame_obj = PERFORMATIVES[frame_type]
    if frame_obj == TransferFrame:
        fields.append(payload)
    return frame_obj(*fields)


def decode_pickle_frame(data):
    # type: (memoryview, int) -> namedtuple
    #_LOGGER.debug("Incoming bytes: %r", data.tobytes())
    buffer = BytesIO(data)
    _ = buffer.read(1)  # First byte is always described type constructor
    frame_constructor = decode_value(buffer)
    fields = decode_value(buffer)
    if frame_constructor == 0x00000014:
        fields.append(buffer)
    return (frame_constructor, fields)


def construct_frame(channel, frame):
    constructor, fields = frame
    return channel, PERFORMATIVES[constructor](*fields)



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
