#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum


TYPE = 'TYPE'
VALUE = 'VALUE'


class AMQPTypes(object):  # pylint: disable=no-init
    null = 'NULL'
    boolean = 'BOOL'
    ubyte = 'UBYTE'
    byte = 'BYTE'
    ushort = 'USHORT'
    short = 'SHORT'
    uint = 'UINT'
    int = 'INT'
    ulong = 'ULONG'
    long = 'LONG'
    float = 'FLOAT'
    double = 'DOUBLE'
    timestamp = 'TIMESTAMP'
    uuid = 'UUID'
    binary = 'BINARY'
    string = 'STRING'
    symbol = 'SYMBOL'
    list = 'LIST'
    map = 'MAP'
    array = 'ARRAY'
    described = 'DESCRIBED'


class FieldDefinition(Enum):
    role = "role"
    sender_settle_mode = "sender-settle-mode"
    receiver_settle_mode = "receiver-settle-mode"
    handle = "handle"
    seconds = "seconds"
    milliseconds = "milliseconds"
    delivery_tag = "delivery-tag"
    delivery_number = "delivery-number"
    transfer_number = "transfer-number"
    sequence_no = "sequence-no"
    message_format = "message-format"
    ietf_language_tag = "ietf-language-tag"
    fields = "fields"
    error = "error"
    sasl_code = "sasl-code"
    annotations = "annotations"
    message_id = "message-id"
    app_properties = "application-properties"
    terminus_durability = "terminus-durability"
    expiry_policy = "terminus-expiry-policy"
    distribution_mode = "distribution-mode"
    node_properties = "node-properties"
    filter_set = "filter-set"


class ObjDefinition(Enum):
    source = "source"
    target = "target"
    delivery_state = "delivery-state"
    error = "error"


class ConstructorBytes(object):  # pylint: disable=no-init
    null = b'\x40'
    bool = b'\x56'
    bool_true = b'\x41'
    bool_false = b'\x42'
    ubyte = b'\x50'
    byte = b'\x51'
    ushort = b'\x60'
    short = b'\x61'
    uint_0 = b'\x43'
    uint_small = b'\x52'
    int_small = b'\x54'
    uint_large = b'\x70'
    int_large = b'\x71'
    ulong_0 = b'\x44'
    ulong_small = b'\x53'
    long_small = b'\x55'
    ulong_large = b'\x80'
    long_large = b'\x81'
    float = b'\x72'
    double = b'\x82'
    timestamp = b'\x83'
    uuid = b'\x98'
    binary_small = b'\xA0'
    binary_large = b'\xB0'
    string_small = b'\xA1'
    string_large = b'\xB1'
    symbol_small = b'\xA3'
    symbol_large = b'\xB3'
    list_0 = b'\x45'
    list_small = b'\xC0'
    list_large = b'\xD0'
    map_small = b'\xC1'
    map_large = b'\xD1'
    array_small = b'\xE0'
    array_large = b'\xF0'
    descriptor = b'\x00'


class SASLCode(Enum):
    #: Connection authentication succeeded.
    ok = 0
    #: Connection authentication failed due to an unspecified problem with the supplied credentials.
    auth = 1
    #: Connection authentication failed due to a system error.
    sys = 2
    #: Connection authentication failed due to a system error that is unlikely to be corrected without intervention.
    sys_perm = 3
    #: Connection authentication failed due to a transient system error.
    sys_temp = 4
