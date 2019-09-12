#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from enum import Enum


TYPE = 'TYPE'
VALUE = 'VALUE'


class AMQPTypes:
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
