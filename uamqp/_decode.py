#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
# pylint: disable=redefined-builtin

import struct
import uuid
from io import BytesIO
from typing import Iterable, Union, Tuple, Dict  # pylint: disable=unused-import

from .types import FieldDefinition, ObjDefinition, ConstructorBytes
from .definitions import _FIELD_DEFINITIONS
from .performatives import (
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
from .endpoints import Source, Target
from .outcomes import (
    Received,
    Accepted,
    Rejected,
    Released,
    Modified,
)

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
}


class DecoderState(object):  # pylint: disable=no-init
    constructor = 'CONSTRUCTOR'
    type_data = 'TYPE_DATA'
    done = 'DONE'


class Decoder(object):

    def __init__(self, length, composite=False):
        self.state = DecoderState.constructor
        self.bytes_remaining = length
        self.decoded_value = {}
        self.constructor_byte = None
        self.composite = composite

    def still_working(self):
        if self.bytes_remaining is None:
            return self.state != DecoderState.done
        return self.bytes_remaining > 0

    def progress(self, num_bytes):
        if self.bytes_remaining is None:
            return
        if self.bytes_remaining - num_bytes < 0:
            raise ValueError("Buffer bytes exhausted.")

        self.bytes_remaining -= num_bytes


def decode_constructor(decoder):
    # type: (Decoder) -> None
    if decoder.constructor_byte == ConstructorBytes.null:
        decoder.decoded_value = None
        decoder.state = DecoderState.done
    elif decoder.constructor_byte == ConstructorBytes.bool_true:
        decoder.decoded_value = True
        decoder.state = DecoderState.done
    elif decoder.constructor_byte == ConstructorBytes.bool_false:
        decoder.decoded_value = False
        decoder.state = DecoderState.done
    elif decoder.constructor_byte in [ConstructorBytes.uint_0, ConstructorBytes.ulong_0]:
        decoder.decoded_value = 0
        decoder.state = DecoderState.done
    else:
        decoder.state = DecoderState.type_data


def _read(buffer, size):
    # type: (IO, int) -> bytes
    data = buffer.read(size)
    if data == b'' or len(data) != size:
        raise ValueError("Buffer exhausted. Read {}, Length: {}".format(data, len(data)))
    return data


def decode_boolean(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    if data == b'\x00':
        decoder.decoded_value = False
    elif data == b'\x01':
        decoder.decoded_value = True
    else:
        raise ValueError("Invalid boolean value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ubyte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid ubyte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ushort(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 2)
    try:
        decoder.decoded_value = struct.unpack('>H', data)[0]
    except Exception:
        raise ValueError("Invalid ushort value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_uint_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_uint_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value = struct.unpack('>I', data)[0]
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_ulong_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ulong_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value = struct.unpack('>Q', data)[0]
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_byte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid byte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_short(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 2)
    try:
        decoder.decoded_value = struct.unpack('>h', data)[0]
    except Exception:
        raise ValueError("Invalid short value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_int_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_int_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value = struct.unpack('>i', data)[0]
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_long_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_long_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value = struct.unpack('>q', data)[0]
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_float(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value = struct.unpack('>f', data)[0]
    except Exception:
        raise ValueError("Invalid float value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_double(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value = struct.unpack('>d', data)[0]
    except Exception:
        raise ValueError("Invalid double value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_timestamp(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value = struct.unpack('>q', data)[0]  # TODO: datetime
    except Exception:
        raise ValueError("Invalid timestamp value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_uuid(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 16)
    try:
        decoder.decoded_value = uuid.UUID(bytes=data)
    except Exception:
        raise ValueError("Invalid UUID value: {}".format(data))
    decoder.progress(16)
    decoder.state = DecoderState.done


def decode_binary_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', _read(buffer, 1))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_binary_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', _read(buffer, 4))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_string_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', _read(buffer, 1))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_string_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', _read(buffer, 4))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_symbol_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', _read(buffer, 1))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_symbol_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', _read(buffer, 4))[0]
    data = _read(buffer, length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_empty_list(decoder, buffer):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = []
    decoder.state = DecoderState.done


def decode_list_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', _read(buffer, 1))[0]
        count = struct.unpack('>B', _read(buffer, 1))[0]
        if decoder.composite:
            items = decode_value(buffer, length_bytes=size - 1, count=count)
        else:
            items = decode_value(buffer, length_bytes=size, count=count)
        decoder.decoded_value = items
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small list.")
    decoder.state = DecoderState.done


def decode_list_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', _read(buffer, 4))[0]
        count = struct.unpack('>L', _read(buffer, 4))[0]
        items = decode_value(buffer, length_bytes=size, count=count)
        decoder.decoded_value = items
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large list.")
    decoder.state = DecoderState.done


def decode_map_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', _read(buffer, 1))[0]
        count = struct.unpack('>B', _read(buffer, 1))[0]
        items = decode_value(buffer, length_bytes=size, count=count)
        decoder.decoded_value = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small map.")
    decoder.state = DecoderState.done


def decode_map_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', _read(buffer, 4))[0]
        count = struct.unpack('>L', _read(buffer, 4))[0]
        items = decode_value(buffer, length_bytes=size, count=count)
        decoder.decoded_value = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large map.")
    decoder.state = DecoderState.done


def decode_array_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', _read(buffer, 1))[0]
        count = struct.unpack('>B', _read(buffer, 1))[0]
        items = decode_value(buffer, length_bytes=size - 1, sub_constructors=False, count=count)
        decoder.decoded_value = items
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small array.")
    decoder.state = DecoderState.done


def decode_array_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', _read(buffer, 4))[0]
        count = struct.unpack('>L', _read(buffer, 4))[0]
        items = decode_value(buffer, length_bytes=size - 4, sub_constructors=False, count=count)
        decoder.decoded_value = items
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large array.")
    decoder.state = DecoderState.done


def decode_described(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        descriptor = decode_value(buffer)
        try:
            composite_type = COMPOSITES[descriptor]
            value = decode_value(buffer, composite=True)
            decoder.decoded_value = (composite_type, value)
        except KeyError:
            value = decode_value(buffer)
            decoder.decoded_value = (descriptor, value)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding described value.")
    decoder.state = DecoderState.done


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
    ConstructorBytes.list_0: decode_empty_list,
    ConstructorBytes.list_small: decode_list_small,
    ConstructorBytes.list_large: decode_list_large,
    ConstructorBytes.map_small: decode_map_small,
    ConstructorBytes.map_large: decode_map_large,
    ConstructorBytes.array_small: decode_array_small,
    ConstructorBytes.array_large: decode_array_large,
    ConstructorBytes.descriptor: decode_described,
}


def decode_value(buffer, length_bytes=None, sub_constructors=True, count=None, composite=False):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    decoder = Decoder(length=length_bytes, composite=composite)
    decoded_values = []

    while decoder.still_working():
        if decoder.state == DecoderState.constructor:
            try:
                decoder.constructor_byte = _read(buffer, 1)
            except ValueError:
                break
            #if decoder.constructor_byte != ConstructorBytes.null:
            decoder.progress(1)
            decode_constructor(decoder)
        elif decoder.state == DecoderState.type_data:
            try:
                _DECODE_MAP[decoder.constructor_byte](decoder, buffer)
            except KeyError:
                raise ValueError("Invalid constructor byte: {}".format(decoder.constructor_byte))
        else:
            raise ValueError("Invalid decoder state {}".format(decoder.state))
        if decoder.state == DecoderState.done and (decoded_values or decoder.bytes_remaining):
            decoded_values.append(decoder.decoded_value)
            if sub_constructors:
                decoder.state = DecoderState.constructor
                decoder.decoded_value = {}
                decoder.constructor_byte = None
            else:
                decoder.state = DecoderState.type_data
                decoder.decoded_value = {}

    if count is not None:
        items = decoded_values or [decoder.decoded_value]
        if len(items) != count:
            raise ValueError("Mismatching length: Expected {} items, received {}.".format(count, len(items)))     
        return items
    return decoded_values or decoder.decoded_value


def decode_empty_frame(header):
    # type: (bytes) -> Performative
    if header[0:4] == b'AMQP':
        layer = header[4]
        if layer == 0:
            return HeaderFrame(header=header)
        if layer == 2:
            return TLSHeaderFrame(header=header)
        if layer == 3:
            return SASLHeaderFrame(header=header)
        raise ValueError("Received unexpected IO layer: {}".format(layer))
    raise ValueError("Received empty frame")


def decode_frame(data, offset):
    # type: (bytes, bytes, bytes) -> Performative
    _ = data[:offset]  # TODO: Extra data
    byte_buffer = BytesIO(data[offset:])
    descriptor, fields = decode_value(byte_buffer)
    frame_type = PERFORMATIVES[descriptor]

    kwargs = {}
    for index, field in enumerate(frame_type.DEFINITION):
        value = fields[index]
        if value is None:
            if field.mandatory:
                raise ValueError("Frame {} missing mandatory field {}".format(frame_type, field.name))
            if field.default is not None:
                value = field.default
        if isinstance(field.type, FieldDefinition):
            if field.multiple:
                kwargs[field.name] = [_FIELD_DEFINITIONS[field.type].decode(v) for v in value] if value else []
            else:
                kwargs[field.name] = _FIELD_DEFINITIONS[field.type].decode(value)
        elif isinstance(field.type, ObjDefinition):
            obj_kwargs = {}
            obj_type, obj_values = value
            for obj_index, obj_value in enumerate(obj_values):
                obj_field = obj_type.DEFINITION[obj_index]
                if isinstance(obj_field.type, FieldDefinition):
                    if obj_field.multiple:
                        obj_kwargs[obj_field.name] = [_FIELD_DEFINITIONS[obj_field.type].decode(v) for v in obj_value] if obj_value else []
                    else:
                        obj_kwargs[obj_field.name] = _FIELD_DEFINITIONS[obj_field.type].decode(obj_value) if obj_value else None
                else:
                    obj_kwargs[obj_field.name] = obj_value
            kwargs[field.name] = obj_type(**obj_kwargs)
        else:
            kwargs[field.name] = value
    return frame_type(**kwargs)
