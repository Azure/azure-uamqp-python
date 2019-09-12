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

    def __init__(self, internal=False):
        self.state = DecoderState.constructor
        self.decoded_value = {}
        self.value_state = None
        self.constructor_byte = None
        self.inner_decoder = None
        self.is_internal = internal
        self.bytes_decoded = 0


def decode_constructor(decoder):
    # type: (Decoder) -> None
    if decoder.constructor_byte == ConstructorBytes.null:
        decoder.decoded_value[TYPE] = AMQPTypes.null
        decoder.decoded_value[VALUE] = None
        decoder.state = DecoderState.constructor
    elif decoder.constructor_byte == ConstructorBytes.bool:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.bool_true:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.decoded_value[VALUE] = True
        decoder.state = DecoderState.constructor
    elif decoder.constructor_byte == ConstructorBytes.bool_false:
        decoder.decoded_value[TYPE] = AMQPTypes.boolean
        decoder.decoded_value[VALUE] = False
        decoder.state = DecoderState.constructor
    elif decoder.constructor_byte == ConstructorBytes.ubyte:
        decoder.decoded_value[TYPE] = AMQPTypes.ubyte
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.ushort:
        decoder.decoded_value[TYPE] = AMQPTypes.ushort
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.uint_0:
        decoder.decoded_value[TYPE] = AMQPTypes.uint
        decoder.decoded_value[VALUE] = 0
        decoder.state = DecoderState.constructor
    elif decoder.constructor_byte in (ConstructorBytes.uint_small, ConstructorBytes.uint_large):
        decoder.decoded_value[TYPE] = AMQPTypes.uint
        decoder.state = DecoderState.type_data
    elif decoder.constructor_byte == ConstructorBytes.ulong_0:
        decoder.decoded_value[TYPE] = AMQPTypes.ulong
        decoder.decoded_value[VALUE] = 0
        decoder.state = DecoderState.constructor
    elif decoder.constructor_byte in (ConstructorBytes.ulong_large, ConstructorBytes.ulong_large):
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
        decoder.state = DecoderState.constructor
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


def decode_boolean(decoder, buffer):
    # type: (Decoder, IO) -> None
    data = buffer.read(1)
    if data == b'\x00':
        decoder.decoded_value[VALUE] = False
    elif data == b'\x01':
        decoder.decoded_value[VALUE] = True
    else:
        raise ValueError("Invalid boolean value: {}".format(data))
    decoder.state = DecoderState.done


def decode_ubyte(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        data = buffer.read(1)
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ubyte value: {}".format(data))
    decoder.state = DecoderState.done


def decode_ushort(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        data = buffer.read(2)
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid ubyte value: {}".format(data))
    decoder.state = DecoderState.done


def decode_uint(decoder, buffer):
    # type: (Decoder, IO) -> None
    try:
        data = buffer.read(4)
        decoder.decoded_value[VALUE] = _from_bytes(data)
    except Exception:
        raise ValueError("Invalid uint value: {}".format(data))
    decoder.state = DecoderState.done


_DECODE_MAP = {
    ConstructorBytes.bool: decode_boolean,
    ConstructorBytes.ubyte: decode_ubyte,
    ConstructorBytes.ushort: decode_ushort
}



def decode_value(buffer, decoder=None):
    # type: (IO, Optional[Decoder]) -> Dict[str, Any]
    decoder = decoder or Decoder()

    while decoder.state != DecoderState.done:
        if decoder.state == DecoderState.constructor:
            if decoder.decoded_value and not decoder.is_internal:
                decoder.decoded_value = {}
            decoder.constructor_byte = buffer.read(1)
            decode_constructor(decoder)
    
        elif decoder.state == DecoderState.type_data:
            try:
                _DECODE_MAP[decoder.constructor_byte](decoder, buffer)
            except KeyError:
                raise ValueError("Invalid constructor byte: {}".format(decoder.constructor_byte))
        else:
            raise ValueError("Invalid decoder state {}".format(decoder.state))
    return decoder.decoded_value
