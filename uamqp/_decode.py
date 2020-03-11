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

from .types import FieldDefinition, ObjDefinition, ConstructorBytes
from .definitions import _FIELD_DEFINITIONS
from .error import AMQPError
from .performatives_tuple import (
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
from .message_tuple import Header, Properties
from .outcomes_tuple import (
    Received,
    Accepted,
    Rejected,
    Released,
    Modified,
)


_LOGGER = logging.getLogger(__name__)
_MESSAGE_PERFORMATIVES = [Header, Properties]
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


class DecoderState(object):  # pylint: disable=no-init
    constructor = 'CONSTRUCTOR'
    type_data = 'TYPE_DATA'
    done = 'DONE'


class Decoder(object):

    def __init__(self, length):
        self.state = DecoderState.constructor
        self.bytes_remaining = length
        self.decoded_value = {}
        self.constructor_byte = None

    def progress(self, num_bytes):
        if self.bytes_remaining is None:
            return
        self.bytes_remaining -= num_bytes


def decode_null(decoder):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = None
    decoder.state = DecoderState.done


def decode_true(decoder):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = True
    decoder.state = DecoderState.done


def decode_false(decoder):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = False
    decoder.state = DecoderState.done


def decode_zero(decoder):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = 0
    decoder.state = DecoderState.done


def decode_empty_list(decoder):
    # type: (Decoder, IO) -> None
    decoder.decoded_value = []
    decoder.state = DecoderState.done


def decode_boolean(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    decoder.decoded_value = data == b'\x01'
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ubyte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid ubyte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ushort(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(2)
    try:
        decoder.decoded_value = struct.unpack('>H', data)[0]
    except Exception:
        raise ValueError("Invalid ushort value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_uint_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_uint_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(4)
    try:
        decoder.decoded_value = struct.unpack('>I', data)[0]
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_ulong_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>B', data)[0]
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ulong_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(8)
    try:
        decoder.decoded_value = struct.unpack('>Q', data)[0]
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_byte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid byte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_short(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(2)
    try:
        decoder.decoded_value = struct.unpack('>h', data)[0]
    except Exception:
        raise ValueError("Invalid short value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_int_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_int_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(4)
    try:
        decoder.decoded_value = struct.unpack('>i', data)[0]
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_long_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    try:
        decoder.decoded_value = struct.unpack('>b', data)[0]
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_long_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(8)
    try:
        decoder.decoded_value = struct.unpack('>q', data)[0]
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_float(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(4)
    try:
        decoder.decoded_value = struct.unpack('>f', data)[0]
    except Exception:
        raise ValueError("Invalid float value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_double(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(8)
    try:
        decoder.decoded_value = struct.unpack('>d', data)[0]
    except Exception:
        raise ValueError("Invalid double value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_timestamp(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(8)
    try:
        decoder.decoded_value = struct.unpack('>q', data)[0]  # TODO: datetime
    except Exception:
        raise ValueError("Invalid timestamp value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_uuid(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(16)
    try:
        decoder.decoded_value = uuid.UUID(bytes=data)
    except Exception:
        raise ValueError("Invalid UUID value: {}".format(data))
    decoder.progress(16)
    decoder.state = DecoderState.done


def decode_binary_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    if length == 0:
        decoder.decoded_value = None
    else:
        data = buffer.read(length)
        try:
            decoder.decoded_value = data
        except Exception:
            raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(1 + length)
    decoder.state = DecoderState.done


def decode_binary_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    if length == 0:
        decoder.decoded_value = None
    else:
        data = buffer.read(length)
        try:
            decoder.decoded_value = data
        except Exception:
            raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(4 + length)
    decoder.state = DecoderState.done


def decode_string_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    data = buffer.read(length)
    try:
        decoder.decoded_value = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(1 + length)
    decoder.state = DecoderState.done


def decode_string_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    data = buffer.read(length)
    try:
        decoder.decoded_value = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(4 + length)
    decoder.state = DecoderState.done


def decode_symbol_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>B', buffer.read(1))[0]
    data = buffer.read(length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(1 + length)
    decoder.state = DecoderState.done


def decode_symbol_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = struct.unpack('>L', buffer.read(4))[0]
    data = buffer.read(length)
    try:
        decoder.decoded_value = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(4 + length)
    decoder.state = DecoderState.done


def decode_list_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', buffer.read(1))[0]
        count = struct.unpack('>B', buffer.read(1))[0]
        items = decode_value(buffer, length_bytes=size - 1, count=count)
        decoder.decoded_value = items
        decoder.progress(2 + size - 1)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small list.")
    decoder.state = DecoderState.done


def decode_list_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', buffer.read(4))[0]
        count = struct.unpack('>L', buffer.read(4))[0]
        items = decode_value(buffer, length_bytes=size - 4, count=count)
        decoder.decoded_value = items
        decoder.progress(8 + size - 4)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large list.")
    decoder.state = DecoderState.done


def decode_map_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', buffer.read(1))[0]
        count = struct.unpack('>B', buffer.read(1))[0]
        items = decode_value(buffer, length_bytes=size - 1, count=count)
        decoder.decoded_value = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(2 + size - 1)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small map.")
    decoder.state = DecoderState.done


def decode_map_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', buffer.read(4))[0]
        count = struct.unpack('>L', buffer.read(4))[0]
        items = decode_value(buffer, length_bytes=size - 4, count=count)
        decoder.decoded_value = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(8 + size - 4)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large map.")
    decoder.state = DecoderState.done


def decode_array_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>B', buffer.read(1))[0]
        count = struct.unpack('>B', buffer.read(1))[0]
        items = decode_value(buffer, length_bytes=size - 1, sub_constructors=False, count=count)
        decoder.decoded_value = items
        decoder.progress(2 + size - 1)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding small array.")
    decoder.state = DecoderState.done


def decode_array_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = struct.unpack('>L', buffer.read(4))[0]
        count = struct.unpack('>L', buffer.read(4))[0]
        items = decode_value(buffer, length_bytes=size - 4, sub_constructors=False, count=count)
        decoder.decoded_value = items
        decoder.progress(8 + size - 4)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding large array.")
    decoder.state = DecoderState.done


def decode_described(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        start_position = buffer.tell()
        descriptor = decode_value(buffer)
        value = decode_value(buffer)
        decoder.decoded_value = (descriptor, value)
        try:
            composite_type = COMPOSITES[descriptor]
            decoder.decoded_value = (composite_type, value)
        except KeyError:
            decoder.decoded_value = (descriptor, value)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding described value.")
    decoder.progress(buffer.tell() - start_position)
    decoder.state = DecoderState.done


def decode_message_section(buffer, message):
    # type: (Decoder, IO) -> None
    descriptor = decode_value(buffer)
    section_type = MESSAGE_SECTIONS[descriptor]
    message[section_type] = decode_value(buffer)


_CONSTUCTOR_MAP = {
    ConstructorBytes.null: decode_null,
    ConstructorBytes.bool_true: decode_true,
    ConstructorBytes.bool_false: decode_false,
    ConstructorBytes.uint_0: decode_zero,
    ConstructorBytes.list_0: decode_empty_list,
    ConstructorBytes.ulong_0: decode_zero,
}
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


def decode_array_values(buffer, count):
    decoded_values = []
    constructor = buffer.read(1)
    try:
        value = _CONSTUCTOR_MAP[constructor]()
        return [value] * count
    except KeyError:
        type_decoder = _DECODE_MAP[constructor]
        for _ in range(count):
            decoded_values.append(type_decoder(buffer))
    return decoded_values



def decode_value(buffer, length_bytes=None, sub_constructors=True, count=None):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    decoder = Decoder(length=length_bytes)
    decoded_values = []

    while decoder.state != DecoderState.done:
        if decoder.state == DecoderState.constructor:
            decoder.constructor_byte = buffer.read(1)
            decoder.progress(1)
            try:
                _CONSTUCTOR_MAP[decoder.constructor_byte](decoder)
            except KeyError:
                decoder.state = DecoderState.type_data

        if decoder.state == DecoderState.type_data:
            _DECODE_MAP[decoder.constructor_byte](decoder, buffer)

        if decoded_values or decoder.bytes_remaining:
            decoded_values.append(decoder.decoded_value)
            if sub_constructors:
                decoder.state = DecoderState.constructor
                decoder.decoded_value = {}
                decoder.constructor_byte = None
            else:
                decoder.state = DecoderState.type_data
                decoder.decoded_value = {}
        if decoder.bytes_remaining == 0:
            break

    if count is not None:
        items = decoded_values or [decoder.decoded_value]
        #if len(items) != count:
        #    raise ValueError("Mismatching length: Expected {} items, received {}.".format(count, len(items)))     
        return items
    return decoded_values or decoder.decoded_value


def decode_empty_frame(header):
    # type: (bytes) -> Performative
    _LOGGER.debug("Empty header bytes: %s", header)
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


def decode_frame(data):
    # type: (memoryview, int) -> namedtuple
    #_LOGGER.debug("Incoming bytes: %r", data.tobytes())
    byte_buffer = BytesIO(data)
    descriptor, fields = decode_value(byte_buffer)
    frame_type = PERFORMATIVES[descriptor]
    if frame_type == TransferFrame:
        fields.append(decode_payload(byte_buffer))
    return frame_type(*fields)
