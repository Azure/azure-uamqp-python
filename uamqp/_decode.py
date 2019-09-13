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


class DecoderState:
    constructor = 'CONSTRUCTOR'
    type_data = 'TYPE_DATA'
    done = 'DONE'


class Decoder:

    def __init__(self, length):
        self.state = DecoderState.constructor
        self.bytes_remaining = length
        self.decoded_value = {}
        self.constructor_byte = None

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
        decoder.decoded_value[TYPE] = AMQPTypes.null
        decoder.decoded_value[VALUE] = None
        decoder.state = DecoderState.done
    elif decoder.constructor_byte == ConstructorBytes.bool:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.bool_true:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.decoded_value[VALUE] = True
        decoder.state = DecoderState.done
    elif decoder.constructor_byte == ConstructorBytes.bool_false:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.decoded_value[VALUE] = False
        decoder.state = DecoderState.done
    elif decoder.constructor_byte == ConstructorBytes.ubyte:
        decoder.decoded_value[TYPE] = AMQPTypes.ubyte
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.ushort:
        decoder.decoded_value[TYPE] = AMQPTypes.ushort
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.uint_0:
        decoder.decoded_value[TYPE] = AMQPTypes.uint
        decoder.decoded_value[VALUE] = 0
        decoder.state = DecoderState.done
    elif decoder.constructor_byte in (ConstructorBytes.uint_small, ConstructorBytes.uint_large):
        decoder.decoded_value[TYPE] = AMQPTypes.uint
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.ulong_0:
        decoder.decoded_value[TYPE] = AMQPTypes.ulong
        decoder.decoded_value[VALUE] = 0
        decoder.state = DecoderState.done
    elif decoder.constructor_byte in (ConstructorBytes.ulong_small, ConstructorBytes.ulong_large):
        decoder.decoded_value[TYPE] = AMQPTypes.ulong
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.byte:
        decoder.decoded_value[TYPE] = AMQPTypes.byte
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.short:
        decoder.decoded_value[TYPE] = AMQPTypes.short
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.int_small, ConstructorBytes.int_large):
        decoder.decoded_value[TYPE] = AMQPTypes.int
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.long_small, ConstructorBytes.long_large):
        decoder.decoded_value[TYPE] = AMQPTypes.long
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.float:
        decoder.decoded_value[TYPE] = AMQPTypes.float
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.double:
        decoder.decoded_value[TYPE] = AMQPTypes.double
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.timestamp:
        decoder.decoded_value[TYPE] = AMQPTypes.timestamp
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.uuid:
        decoder.decoded_value[TYPE] = AMQPTypes.uuid
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.binary_small, ConstructorBytes.binary_large):
        decoder.decoded_value[TYPE] = AMQPTypes.binary
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.string_small, ConstructorBytes.string_large):
        decoder.decoded_value[TYPE] = AMQPTypes.string
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.symbol_small, ConstructorBytes.symbol_large):
        decoder.decoded_value[TYPE] = AMQPTypes.symbol
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.list_0:
        decoder.decoded_value[TYPE] = AMQPTypes.list
        decoder.decoded_value[VALUE] = []
        decoder.state = DecoderState.done
    elif decoder.constructor_byte in (ConstructorBytes.list_small, ConstructorBytes.list_large):
        decoder.decoded_value[TYPE] = AMQPTypes.list
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.map_small, ConstructorBytes.map_large):
        decoder.decoded_value[TYPE] = AMQPTypes.map
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte in (ConstructorBytes.array_small, ConstructorBytes.array_large):
        decoder.decoded_value[TYPE] = AMQPTypes.map
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.descriptor:
        decoder.decoded_value[TYPE] = AMQPTypes.described
        decoder.state = DecoderState.type_data
    else:
        raise ValueError("Invalid constructor byte: {}".format(decoder.constructor_byte))


def _from_bytes(data, signed=False):
    # type: (bytes) -> int
    return int.from_bytes(data, 'big', signed=signed)


def _read(buffer, size):
    # type: (IO, int) -> bytes
    data = buffer.read(size)
    if data == b'' or len(data) != size:
        raise ValueError("Buffer exhausted")
    return data


def decode_boolean(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    if data == b'\x00':
        decoder.decoded_value[VALUE] = False
    elif data == b'\x01':
        decoder.decoded_value[VALUE] = True
    else:
        raise ValueError("Invalid boolean value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ubyte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ubyte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ushort(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 2)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ushort value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_uint_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_uint_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_ulong_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_ulong_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ulong value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_byte(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid byte value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_short(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 2)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid short value: {}".format(data))
    decoder.progress(2)
    decoder.state = DecoderState.done


def decode_int_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_int_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid int value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_long_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 1)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(1)
    decoder.state = DecoderState.done


def decode_long_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)
    except Exception:
        raise ValueError("Invalid long value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_float(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 4)
    try:
        decoder.decoded_value[VALUE] = struct.unpack('>f', data)[0]
    except Exception:
        raise ValueError("Invalid float value: {}".format(data))
    decoder.progress(4)
    decoder.state = DecoderState.done


def decode_double(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value[VALUE] =struct.unpack('>d', data)[0]
    except Exception:
        raise ValueError("Invalid double value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_timestamp(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 8)
    try:
        decoder.decoded_value[VALUE] = _from_bytes(data, signed=True)  # TODO: datetime
    except Exception:
        raise ValueError("Invalid timestamp value: {}".format(data))
    decoder.progress(8)
    decoder.state = DecoderState.done


def decode_uuid(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = _read(buffer, 16)
    try:
        decoder.decoded_value[VALUE] = uuid.UUID(bytes=data)
    except Exception:
        raise ValueError("Invalid UUID value: {}".format(data))
    decoder.progress(16)
    decoder.state = DecoderState.done


def decode_binary_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 1))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data
    except Exception:
        raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_binary_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 4))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data
    except Exception:
        raise ValueError("Error reading binary data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_string_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 1))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_string_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 4))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data.decode('utf-8')
    except Exception:
        raise ValueError("Error reading string data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_symbol_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 1))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(1)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_symbol_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    length = _from_bytes(_read(buffer, 4))
    data = _read(buffer, length)
    try:
        decoder.decoded_value[VALUE] = data
    except Exception:
        raise ValueError("Error reading symbol data: {}".format(data))
    decoder.progress(4)
    decoder.progress(length)
    decoder.state = DecoderState.done


def decode_list_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 1))
        count = _from_bytes(_read(buffer, 1))
        items = decode_value(buffer, size)
        if len(items) != count:
            raise ValueError("Mismatching list length.")
        decoder.decoded_value[VALUE] = items
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding list.")
    decoder.state = DecoderState.done


def decode_list_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 4))
        count = _from_bytes(_read(buffer, 4))
        items = decode_value(buffer, size)
        if len(items) != count:
            raise ValueError("Mismatching list length.")
        decoder.decoded_value[VALUE] = items
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding list.")
    decoder.state = DecoderState.done


def decode_map_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 1))
        count = _from_bytes(_read(buffer, 1))
        items = decode_value(buffer, size)
        if len(items) != count or count % 2 != 0:
            raise ValueError("Mismatching map length.")
        decoder.decoded_value[VALUE] = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding map.")
    decoder.state = DecoderState.done


def decode_map_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 4))
        count = _from_bytes(_read(buffer, 4))
        items = decode_value(buffer, size)
        if len(items) != count or count % 2 != 0:
            raise ValueError("Mismatching map length.")
        decoder.decoded_value[VALUE] = [(items[i], items[i+1]) for i in range(0, len(items), 2)]
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding map.")
    decoder.state = DecoderState.done


def decode_array_small(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 1))
        count = _from_bytes(_read(buffer, 1))
        items = decode_value(buffer, size, sub_constructors=False)
        if len(items) != count:
            raise ValueError("Mismatching list length.")
        decoder.decoded_value[VALUE] = items
        decoder.progress(2)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding list.")
    decoder.state = DecoderState.done


def decode_array_large(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        size = _from_bytes(_read(buffer, 4))
        count = _from_bytes(_read(buffer, 4))
        items = decode_value(buffer, size, sub_constructors=False)
        if len(items) != count:
            raise ValueError("Mismatching list length.")
        decoder.decoded_value[VALUE] = items
        decoder.progress(8)
        decoder.progress(size)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding list.")
    decoder.state = DecoderState.done


def decode_described(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        descriptor = decode_value(buffer)
        value = decode_value(buffer)
        decoder.decoded_value[VALUE] = (descriptor, value)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Error decoding list.")
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
    ConstructorBytes.list_small: decode_list_small,
    ConstructorBytes.list_large: decode_list_large,
    ConstructorBytes.map_small: decode_map_small,
    ConstructorBytes.map_large: decode_map_large,
    ConstructorBytes.array_small: decode_array_small,
    ConstructorBytes.array_large: decode_array_large,
    ConstructorBytes.descriptor: decode_described,
}


def decode_value(buffer, length_bytes=None, sub_constructors=True):
    # type: (IO, Optional[int], bool) -> Dict[str, Any]
    decoder = Decoder(length=length_bytes)
    decoded_values = []

    while decoder.still_working():
        if decoder.state == DecoderState.constructor:
            try:
                decoder.constructor_byte = _read(buffer, 1)
            except ValueError:
                break
            if decoder.constructor_byte != ConstructorBytes.null:
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

    return decoded_values or decoder.decoded_value
