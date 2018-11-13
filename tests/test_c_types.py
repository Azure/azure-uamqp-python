# -- coding: utf-8 --
#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import uuid
import six
import functools

root_path = os.path.realpath('.')
sys.path.append(root_path)

from uamqp import types


def test_symbol_type():

    binary_type = functools.partial(six.binary_type, encoding='UTF-8') if six.PY3  else six.binary_type

    test_symbol = types.AMQPSymbol("testvalue")
    assert test_symbol.value == b"testvalue"
    assert test_symbol.c_data.value == b"testvalue"
    assert str(test_symbol.c_data) == "testvalue"
    assert bytes(test_symbol.c_data) == b"testvalue"

    test_symbol = types.AMQPSymbol(b"testvalue")
    assert test_symbol.c_data.value == b"testvalue"
    assert str(test_symbol.c_data) == "testvalue"
    assert bytes(test_symbol.c_data) == b"testvalue"

    test_symbol = types.AMQPSymbol(u"testvalue")
    assert test_symbol.c_data.value == b"testvalue"
    assert str(test_symbol.c_data) == "testvalue"
    assert bytes(test_symbol.c_data) == b"testvalue"

    test_symbol = types.AMQPSymbol(u"é,è,à,ù,â,ê,î,ô,û")
    assert test_symbol.c_data.value == binary_type("é,è,à,ù,â,ê,î,ô,û")
    assert str(test_symbol.c_data) == "é,è,à,ù,â,ê,î,ô,û"
    assert bytes(test_symbol.c_data) == binary_type("é,è,à,ù,â,ê,î,ô,û")

    test_symbol = types.AMQPSymbol("é,è,à,ù,â,ê,î,ô,û")
    assert test_symbol.c_data.value == binary_type("é,è,à,ù,â,ê,î,ô,û")
    assert str(test_symbol.c_data) == "é,è,à,ù,â,ê,î,ô,û"
    assert bytes(test_symbol.c_data) == binary_type("é,è,à,ù,â,ê,î,ô,û")

    try:
        test_str = (
            "\xe5\x95\x8a\xe9\xbd\x84\xe4\xb8\x82\xe7\x8b\x9b\xe7\x8b"
            "\x9c\xef\xa7\xb1\xef\xa4\xac\xef\xa7\xb1\xef\xa8\x8c\xef"
            "\xa8\xa9\xcb\x8a\xe3\x80\x9e\xe3\x80\xa1\xef\xbf\xa4\xe2"
            "\x84\xa1\xe3\x88\xb1\xe2\x80\x90\xe3\x83\xbc\xef\xb9\xa1"
            "\xef\xb9\xa2\xef\xb9\xab\xe3\x80\x81\xe3\x80\x93\xe2\x85"
            "\xb0\xe2\x85\xb9\xe2\x92\x88\xe2\x82\xac\xe3\x88\xa0\xe3"
            "\x88\xa9\xe2\x85\xa0\xe2\x85\xab\xef\xbc\x81\xef\xbf\xa3"
            "\xe3\x81\x81\xe3\x82\x93\xe3\x82\xa1\xe3\x83\xb6\xce\x91"
            "\xef\xb8\xb4\xd0\x90\xd0\xaf\xd0\xb0\xd1\x8f\xc4\x81\xc9"
            "\xa1\xe3\x84\x85\xe3\x84\xa9\xe2\x94\x80\xe2\x95\x8b\xef"
            "\xb8\xb5\xef\xb9\x84\xef\xb8\xbb\xef\xb8\xb1\xef\xb8\xb3"
            "\xef\xb8\xb4\xe2\x85\xb0\xe2\x85\xb9\xc9\x91\xee\x9f\x87"
            "\xc9\xa1\xe3\x80\x87\xe3\x80\xbe\xe2\xbf\xbb\xe2\xba\x81"
            "\xee\xa1\x83\xe4\x9c\xa3\xee\xa1\xa4\xe2\x82\xac")
        decoded = test_str.decode('utf-8')

    except AttributeError:
        test_str = (
            b"\xe5\x95\x8a\xe9\xbd\x84\xe4\xb8\x82\xe7\x8b\x9b\xe7\x8b"
            b"\x9c\xef\xa7\xb1\xef\xa4\xac\xef\xa7\xb1\xef\xa8\x8c\xef"
            b"\xa8\xa9\xcb\x8a\xe3\x80\x9e\xe3\x80\xa1\xef\xbf\xa4\xe2"
            b"\x84\xa1\xe3\x88\xb1\xe2\x80\x90\xe3\x83\xbc\xef\xb9\xa1"
            b"\xef\xb9\xa2\xef\xb9\xab\xe3\x80\x81\xe3\x80\x93\xe2\x85"
            b"\xb0\xe2\x85\xb9\xe2\x92\x88\xe2\x82\xac\xe3\x88\xa0\xe3"
            b"\x88\xa9\xe2\x85\xa0\xe2\x85\xab\xef\xbc\x81\xef\xbf\xa3"
            b"\xe3\x81\x81\xe3\x82\x93\xe3\x82\xa1\xe3\x83\xb6\xce\x91"
            b"\xef\xb8\xb4\xd0\x90\xd0\xaf\xd0\xb0\xd1\x8f\xc4\x81\xc9"
            b"\xa1\xe3\x84\x85\xe3\x84\xa9\xe2\x94\x80\xe2\x95\x8b\xef"
            b"\xb8\xb5\xef\xb9\x84\xef\xb8\xbb\xef\xb8\xb1\xef\xb8\xb3"
            b"\xef\xb8\xb4\xe2\x85\xb0\xe2\x85\xb9\xc9\x91\xee\x9f\x87"
            b"\xc9\xa1\xe3\x80\x87\xe3\x80\xbe\xe2\xbf\xbb\xe2\xba\x81"
            b"\xee\xa1\x83\xe4\x9c\xa3\xee\xa1\xa4\xe2\x82\xac")
        decoded = test_str.decode('utf-8')

    test_symbol = types.AMQPSymbol(test_str)
    assert test_symbol.c_data.value == test_str
    assert str(test_symbol.c_data) == decoded if six.PY3 else test_str
    assert bytes(test_symbol.c_data) == test_str

    test_symbol = types.AMQPSymbol(decoded)
    assert test_symbol.c_data.value == test_str
    assert str(test_symbol.c_data) == decoded if six.PY3 else test_str
    assert bytes(test_symbol.c_data) == test_str

    test_str = "黃帝者，少典之子，姓公孫，名曰軒轅。生而神靈，弱而能言，幼而徇齊，長而敦敏，成而聰明。"
    decoded = test_str.decode('utf-8') if six.PY2 else test_str

    test_symbol = types.AMQPSymbol(test_str)
    assert test_symbol.c_data.value == binary_type(test_str)
    assert str(test_symbol.c_data) == decoded if six.PY3 else test_str
    assert bytes(test_symbol.c_data) == binary_type(test_str)

    test_symbol = types.AMQPSymbol(decoded)
    assert test_symbol.c_data.value == binary_type(test_str)
    assert str(test_symbol.c_data) == decoded if six.PY3 else test_str
    assert bytes(test_symbol.c_data) == binary_type(test_str)


if __name__ == '__main__':
    test_symbol_type()