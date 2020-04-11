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

try:
    from uamqp_encoder.c_uamqp import decode_frame as c_decode_frame
except ImportError:
    c_decode_frame = None
c_decode_frame = None

from uamqp.types import ConstructorBytes
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


_LOGGER = logging.getLogger(__name__)
_HEADER_PREFIX = memoryview(b'AMQP')


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


# COMPOSITES = {
#     0x00000023: Received,
#     0x00000024: Accepted,
#     0x00000025: Rejected,
#     0x00000026: Released,
#     0x00000027: Modified,
#     0x00000028: Source,
#     0x00000029: Target,
#     0x0000001d: AMQPError,
# }

COMPOSITES = {
    0x00000023: 'received',
    0x00000024: 'accepted',
    0x00000025: 'rejected',
    0x00000026: 'released',
    0x00000027: 'modified',
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


def decode_value(buffer, constructor=None):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    constructor = constructor or buffer.read(1)
    if constructor == ConstructorBytes.null:
        return None
    if constructor == ConstructorBytes.bool_true:
        return True
    if constructor == ConstructorBytes.bool_false:
        return False
    if constructor == ConstructorBytes.uint_0:
        return 0
    if constructor == ConstructorBytes.list_0:
        return []
    if constructor == ConstructorBytes.ulong_0:
        return 0
    if constructor == ConstructorBytes.bool:
        return buffer.read(1) == b'\x01'
    if constructor == ConstructorBytes.ubyte:
        return struct.unpack('>B', buffer.read(1))[0]
    if constructor == ConstructorBytes.ushort:
        return struct.unpack('>H', buffer.read(2))[0]
    if constructor == ConstructorBytes.uint_small:
        return struct.unpack('>B', buffer.read(1))[0]
    if constructor == ConstructorBytes.uint_large:
        return struct.unpack('>I', buffer.read(4))[0]
    if constructor == ConstructorBytes.ulong_small:
        return struct.unpack('>B', buffer.read(1))[0]
    if constructor == ConstructorBytes.ulong_large:
        return struct.unpack('>Q', buffer.read(8))[0]
    if constructor == ConstructorBytes.byte:
        return struct.unpack('>b', buffer.read(1))[0]
    if constructor == ConstructorBytes.short:
        return struct.unpack('>h', buffer.read(2))[0]
    if constructor == ConstructorBytes.int_small:
        return struct.unpack('>b', buffer.read(1))[0]
    if constructor == ConstructorBytes.int_large:
        return struct.unpack('>i', buffer.read(4))[0]
    if constructor == ConstructorBytes.long_small:
        return struct.unpack('>b', buffer.read(1))[0]
    if constructor == ConstructorBytes.long_large:
        return struct.unpack('>q', buffer.read(8))[0]
    if constructor == ConstructorBytes.float:
        return struct.unpack('>f', buffer.read(4))[0]
    if constructor == ConstructorBytes.double:
        return struct.unpack('>d', buffer.read(8))[0]
    if constructor == ConstructorBytes.timestamp:
        return struct.unpack('>q', buffer.read(8))[0]
    if constructor == ConstructorBytes.uuid:
        return uuid.UUID(bytes=buffer.read(16))
    if constructor == ConstructorBytes.binary_small:
        length = struct.unpack('>B', buffer.read(1))[0]
        return buffer.read(length) or None
    if constructor == ConstructorBytes.binary_large:
        length = struct.unpack('>L', buffer.read(4))[0]
        return buffer.read(length) or None
    if constructor == ConstructorBytes.string_small:
        length = struct.unpack('>B', buffer.read(1))[0]
        return buffer.read(length).decode('utf-8') or None
    if constructor == ConstructorBytes.string_large:
        length = struct.unpack('>L', buffer.read(4))[0]
        return buffer.read(length).decode('utf-8') or None
    if constructor == ConstructorBytes.symbol_small:
        length = struct.unpack('>B', buffer.read(1))[0]
        return buffer.read(length) or None
    if constructor == ConstructorBytes.symbol_large:
        length = struct.unpack('>L', buffer.read(4))[0]
        return buffer.read(length) or None
    if constructor == ConstructorBytes.list_small:
        _ = buffer.read(1)  # Discard size
        count = struct.unpack('>B', buffer.read(1))[0]
        return [decode_value(buffer) for _ in range(count)]
    if constructor == ConstructorBytes.list_large:
        _ = buffer.read(4)  # Discard size
        count = struct.unpack('>L', buffer.read(4))[0]
        return [decode_value(buffer) for _ in range(count)]
    if constructor == ConstructorBytes.map_small:
        _ = buffer.read(1)  # Discard size
        count = struct.unpack('>B', buffer.read(1))[0]
        return {decode_value(buffer): decode_value(buffer) for _ in range(0, count, 2)}
    if constructor == ConstructorBytes.map_large:
        _ = buffer.read(4)  # Discard size
        count = struct.unpack('>L', buffer.read(4))[0]
        return {decode_value(buffer): decode_value(buffer) for _ in range(0, count, 2)}
    if constructor == ConstructorBytes.array_small:
        _ = buffer.read(1)  # Discard size
        count = struct.unpack('>B', buffer.read(1))[0]
        subconstructor = buffer.read(1)
        return [decode_value(buffer, subconstructor) for _ in range(count)]
    if constructor == ConstructorBytes.array_large:
        _ = buffer.read(4)  # Discard size
        count = struct.unpack('>L', buffer.read(4))[0]
        subconstructor = buffer.read(1)
        return [decode_value(buffer, subconstructor) for _ in range(count)]
    if constructor == ConstructorBytes.descriptor:
        descriptor = decode_value(buffer)
        value = decode_value(buffer)
        try:
            composite_type = COMPOSITES[descriptor]
            return {composite_type: value}
        except KeyError:
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
    if header[5] == 0:
        return "EMPTY"
    raise ValueError("Received unrecognized empty frame")


def decode_payload(buffer):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    message = {}
    while True:
        constructor = buffer.read(1)
        if constructor:
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
        else:
            break  # Finished stream
    return message


def py_decode_frame(data):
    buffer = BytesIO(data)
    _ = buffer.read(1)  # First byte is always described type constructor
    frame_type = decode_value(buffer)
    fields = decode_value(buffer)

    frame_obj = PERFORMATIVES[frame_type]
    if frame_obj == TransferFrame:
        fields.append(decode_payload(buffer))
    return frame_obj, fields


def decode_frame(size, data):
    # type: (int, memoryview) -> namedtuple
    #_LOGGER.debug("Incoming bytes: %r", data.tobytes())
    if c_decode_frame:
        frame_type, fields = c_decode_frame(size, data.tobytes())
        frame_obj = PERFORMATIVES[frame_type]
    else:
        frame_obj, fields = py_decode_frame(data)

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
