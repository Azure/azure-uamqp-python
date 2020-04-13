#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import datetime
import uuid

from uamqp import _decode as decode
from uamqp.types import AMQPTypes, TYPE, VALUE

import pytest


def decode_value(buffer):
    return decode._DECODE_BY_CONSTRUCTOR[buffer[0]](buffer[1:])

def test_decode_null():
    buffer = memoryview(b"\x40")
    _, output = decode_value(buffer)
    assert output == None

    # buffer = memoryview(b"\x40\x40")
    # output = decode_value(buffer, length_bytes=2)
    # assert output == [None, None]


def test_decode_boolean():
    buffer = memoryview(b"\x56\x00")
    _, output = decode_value(buffer)
    assert output == False

    buffer = memoryview(b"\x56\x01")
    _, output = decode_value(buffer)
    assert output == True

    buffer = memoryview(b"\x41")
    _, output = decode_value(buffer)
    assert output == True

    buffer = memoryview(b"\x42")
    _, output = decode_value(buffer)
    assert output == False

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x56")
    #     decode_value(buffer)

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x56\x02")
    #     decode_value(buffer)


def test_decode_ubyte():
    buffer = memoryview(b"\x50\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x50\xFF")
    _, output = decode_value(buffer)
    assert output == 255

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x50")
    #     decode_value(buffer)


def test_decode_ushort():
    buffer = memoryview(b"\x60\x00\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x60\xFF\xFF")
    _, output = decode_value(buffer)
    assert output == 65535

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x60\x00")
    #     decode_value(buffer)


def test_decode_uint():
    buffer = memoryview(b"\x70\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x70\x42\x43\x44\x45")
    _, output = decode_value(buffer)
    assert output == 1111704645

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x70\x42\x43")
    #     decode_value(buffer)

    buffer = memoryview(b"\x52\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x52\xFF")
    _, output = decode_value(buffer)
    assert output == 255

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x52")
    #     decode_value(buffer)

    buffer = memoryview(b"\x43")
    _, output = decode_value(buffer)
    assert output == 0


def test_decode_ulong():
    buffer = memoryview(b"\x80\x00\x00\x00\x00\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x80\x42\x43\x44\x45\x46\x47\x48\x49")
    _, output = decode_value(buffer)
    assert output == 4774735094265366601

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x80\x42\x43\x44\x45\x46\x47")
    #     decode_value(buffer)

    buffer = memoryview(b"\x53\x00")
    _, output = decode_value(buffer)
    assert output == 0

    buffer = memoryview(b"\x53\xFF")
    _, output = decode_value(buffer)
    assert output == 255

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x53")
    #     decode_value(buffer)

    buffer = memoryview(b"\x44")
    _, output = decode_value(buffer)
    assert output == 0


def test_decode_byte():
    buffer = memoryview(b"\x51\x80")
    _, output = decode_value(buffer)
    assert output == -128

    buffer = memoryview(b"\x51\x7F")
    _, output = decode_value(buffer)
    assert output == 127

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x51")
    #     decode_value(buffer)


def test_decode_short():
    buffer = memoryview(b"\x61\x80\x00")
    _, output = decode_value(buffer)
    assert output == -32768

    buffer = memoryview(b"\x61\x7F\xFF")
    _, output = decode_value(buffer)
    assert output == 32767

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x61\x7F")
    #     decode_value(buffer)


def test_decode_int():
    buffer = memoryview(b"\x71\x80\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == -2147483648

    buffer = memoryview(b"\x71\x7F\xFF\xFF\xFF")
    _, output = decode_value(buffer)
    assert output == 2147483647

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x71\x7F\xFF\xFF")
    #     decode_value(buffer)

    buffer = memoryview(b"\x54\x80")
    _, output = decode_value(buffer)
    assert output == -128

    buffer = memoryview(b"\x54\x7F")
    _, output = decode_value(buffer)
    assert output == 127

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x54")
    #     decode_value(buffer)


def test_decode_long():
    buffer = memoryview(b"\x81\x80\x00\x00\x00\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == -9223372036854775808

    buffer = memoryview(b"\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    _, output = decode_value(buffer)
    assert output == 9223372036854775807

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x81\x7F\xFF\xFF\xFF\xFF\xFF\xFF")
    #     decode_value(buffer)

    buffer = memoryview(b"\x55\x80")
    _, output = decode_value(buffer)
    assert output == -128

    buffer = memoryview(b"\x55\x7F")
    _, output = decode_value(buffer)
    assert output == 127

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x55")
    #     decode_value(buffer)


def test_decode_float():
    buffer = memoryview(b"\x72\xBF\x80\x00\x00")
    _, output = decode_value(buffer)
    assert output == -1.0

    buffer = memoryview(b"\x72\x42\x28\x00\x00")
    _, output = decode_value(buffer)
    assert output == 42.0

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x72\x42")
    #     decode_value(buffer)


def test_decode_double():
    buffer = memoryview(b"\x82\x40\x45\x00\x00\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == 42.0

    buffer = memoryview(b"\x82\xBF\xF0\x00\x00\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == -1.0

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x82\x40\x45")
    #     decode_value(buffer)


def test_decode_timestamp():
    buffer = memoryview(b"\x83\x80\x00\x00\x00\x00\x00\x00\x00")
    _, output = decode_value(buffer)
    assert output == -9223372036854775808

    buffer = memoryview(b"\x83\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")
    _, output = decode_value(buffer)
    assert output == 9223372036854775807

    # with pytest.raises(ValueError):
    #     buffer = memoryview(b"\x83\x7F\xFF\xFF\xFF\xFF\xFF\xFF")
    #     decode_value(buffer)

"""


/* Tests_SRS_AMQPVALUE_01_370: [1.6.18 uuid A universally unique identifier as defined by RFC-4122 section 4.1.2 .] */
/* Tests_SRS_AMQPVALUE_01_371: [<encoding code="0x98" category="fixed" width="16" label="UUID as defined in section 4.1.2 of RFC-4122"/>] */
TEST_FUNCTION(amqpvalue_decode_uuid_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0x98, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18 };
    uuid expected_uuid = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18 };
    uuid actual_value = { 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_UUID, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_uuid(decoded_values[0], &actual_value);
    stringify_bytes(actual_value, sizeof(actual_value), actual_stringified);
    stringify_bytes(expected_uuid, sizeof(expected_uuid), expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_370: [1.6.18 uuid A universally unique identifier as defined by RFC-4122 section 4.1.2 .] */
/* Tests_SRS_AMQPVALUE_01_371: [<encoding code="0x98" category="fixed" width="16" label="UUID as defined in section 4.1.2 of RFC-4122"/>] */
TEST_FUNCTION(amqpvalue_decode_uuid_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0x98, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18 };
    uuid expected_uuid = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18 };
    int i;
    uuid actual_value = { 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_UUID, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_uuid(decoded_values[0], &actual_value);
    stringify_bytes(actual_value, sizeof(actual_value), actual_stringified);
    stringify_bytes(expected_uuid, sizeof(expected_uuid), expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_uuid_not_enough_bytes_does_not_trigger_a_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0x98, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_zero_size_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA0, 0x00 };
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(bytes, 0, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_one_byte_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA0, 0x01, 0x42 };
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[2], sizeof(bytes) - 2, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_255_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 2] = { 0xA0, 0xFF };
    unsigned int i;
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    for (i = 0; i < 255; i++)
    {
        bytes[2 + i] = (unsigned char)i;
    }

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[2], sizeof(bytes) - 2, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_255_bytes_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 2] = { 0xA0, 0xFF };
    unsigned int i;
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    for (i = 0; i < 255; i++)
    {
        bytes[2 + i] = (unsigned char)i;
    }

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[2], sizeof(bytes) - 2, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_zero_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_one_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA0, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_allocating_memory_fails_then_amqpvalue_decode_binary_one_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA0, 0x01, 0x42 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_255_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[254 + 2] = { 0xA0, 0xFF };
    unsigned int i;
    umock_c_reset_all_calls();

    for (i = 0; i < 254; i++)
    {
        bytes[2 + i] = (unsigned char)i;
    }

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_value_zero_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB0, 0x00, 0x00, 0x00, 0x00 };
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[0], 0, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_value_1_byte_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB0, 0x00, 0x00, 0x00, 0x01, 0x42 };
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[5], sizeof(bytes) - 5, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_372: [1.6.19 binary A sequence of octets.] */
/* Tests_SRS_AMQPVALUE_01_373: [<encoding name="vbin8" code="0xa0" category="variable" width="1" label="up to 2^8 - 1 octets of binary data"/>] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_value_256_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[256 + 5] = { 0xB0, 0x00, 0x00, 0x01, 0x00 };
    int i;
    amqp_binary actual_value = { NULL, 0 };
    umock_c_reset_all_calls();

    for (i = 0; i < 256; i++)
    {
        bytes[5 + i] = i & 0xFF;
    }

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_BINARY, (int)amqpvalue_get_type(decoded_values[0]));
    amqpvalue_get_binary(decoded_values[0], &actual_value);
    stringify_bytes((const unsigned char*)actual_value.bytes, actual_value.length, actual_stringified);
    stringify_bytes(&bytes[5], sizeof(bytes) - 5, expected_stringified);
    ASSERT_ARE_EQUAL(char_ptr, expected_stringified, actual_stringified);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_zero_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB0 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_1_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB0, 0x00, 0x00, 0x00, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_allocating_fails_then_amqpvalue_decode_binary_0xB0_1_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB0, 0x00, 0x00, 0x00, 0x01, 0x42 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_binary_0xB0_256_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 5] = { 0xB0, 0x00, 0x00, 0x01, 0x00 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_376: [<encoding name="str8-utf8" code="0xa1" category="variable" width="1" label="up to 2^8 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_value_zero_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1, 0x00 };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_376: [<encoding name="str8-utf8" code="0xa1" category="variable" width="1" label="up to 2^8 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_value_1_byte_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1, 0x01, 'a' };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "a", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_376: [<encoding name="str8-utf8" code="0xa1" category="variable" width="1" label="up to 2^8 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_value_255_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 2] = { 0xA1, 0xFF, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 2, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_376: [<encoding name="str8-utf8" code="0xa1" category="variable" width="1" label="up to 2^8 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_value_2_bytes_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1, 0x02, 'a', 'b' };
    int i;
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "ab", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_zero_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_one_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_allocating_memory_fails_amqpvalue_decode_string_0xA1_one_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA1, 0x01, 'a' };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xA1_255_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[254 + 2] = { 0xA1, 0xFF, 'x' };
    umock_c_reset_all_calls();

    (void)memset(bytes + 2, 'x', 254);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_377: [<encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_value_zero_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1, 0x00, 0x00, 0x00, 0x00 };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_377: [<encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_value_1_byte_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1, 0x00, 0x00, 0x00, 0x01, 'a' };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "a", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_377: [<encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_value_255_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 5] = { 0xB1, 0x00, 0x00, 0x00, 0xFF, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_377: [<encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_value_256_bytes_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[256 + 5] = { 0xB1, 0x00, 0x00, 0x01, 0x00, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 256);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_375: [1.6.20 string A sequence of Unicode characters.] */
/* Tests_SRS_AMQPVALUE_01_377: [<encoding name="str32-utf8" code="0xb1" category="variable" width="4" label="up to 2^32 - 1 octets worth of UTF-8 Unicode (with no byte order mark)"/>] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_value_2_bytes_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1, 0x00, 0x00, 0x00, 0x02, 'a', 'b' };
    int i;
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_STRING, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_string(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "ab", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_zero_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_one_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1, 0x00, 0x00, 0x00, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_string_0xB1_255_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 5] = { 0xB1, 0x00, 0x00, 0x01, 0x00, 'x' };
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_gballoc_malloc_fails_then_amqpvalue_decode_string_0xB1_one_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB1, 0x00, 0x00, 0x00, 0x01, 'a' };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_379: [<encoding name="sym8" code="0xa3" category="variable" width="1" label="up to 2^8 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_value_zero_chars_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3, 0x00 };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_379: [<encoding name="sym8" code="0xa3" category="variable" width="1" label="up to 2^8 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_value_1_char_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3, 0x01, 'a' };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "a", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_379: [<encoding name="sym8" code="0xa3" category="variable" width="1" label="up to 2^8 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_value_255_chars_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 2] = { 0xA3, 0xFF, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 2, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_379: [<encoding name="sym8" code="0xa3" category="variable" width="1" label="up to 2^8 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_value_2_chars_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3, 0x02, 'a', 'b' };
    int i;
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "ab", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_zero_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_one_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_allocating_memory_fails_amqpvalue_decode_symbol_0xA3_one_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xA3, 0x01, 'a' };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xA3_255_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[254 + 2] = { 0xA3, 0xFF, 'x' };
    umock_c_reset_all_calls();

    (void)memset(bytes + 2, 'x', 254);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_380: [<encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_value_zero_chars_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3, 0x00, 0x00, 0x00, 0x00 };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_380: [<encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_value_1_char_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3, 0x00, 0x00, 0x00, 0x01, 'a' };
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "a", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_380: [<encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_value_255_chars_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 5] = { 0xB3, 0x00, 0x00, 0x00, 0xFF, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_380: [<encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_value_256_chars_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[256 + 5] = { 0xB3, 0x00, 0x00, 0x01, 0x00, 'x' };
    const char* actual_value;
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 256);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" "xxxxxx", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_378: [1.6.21 symbol Symbolic values from a constrained domain.] */
/* Tests_SRS_AMQPVALUE_01_380: [<encoding name="sym32" code="0xb3" category="variable" width="4" label="up to 2^32 - 1 seven bit ASCII characters representing a symbolic value"/>] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_value_2_chars_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3, 0x00, 0x00, 0x00, 0x02, 'a', 'b' };
    int i;
    const char* actual_value;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_SYMBOL, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_symbol(decoded_values[0], &actual_value);
    ASSERT_ARE_EQUAL(char_ptr, "ab", actual_value);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_zero_bytes_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_one_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3, 0x00, 0x00, 0x00, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_symbol_0xB3_255_byte_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[255 + 5] = { 0xB3, 0x00, 0x00, 0x01, 0x00, 'x' };
    umock_c_reset_all_calls();

    (void)memset(bytes + 5, 'x', 255);

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_326: [If any allocation failure occurs during decoding, amqpvalue_decode_bytes shall fail and return a non-zero value.] */
TEST_FUNCTION(when_gballoc_malloc_fails_then_amqpvalue_decode_symbol_0xB3_one_byte_fails)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xB3, 0x00, 0x00, 0x00, 0x01, 'a' };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .SetReturn(NULL);

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_NOT_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_384: [<encoding name="list0" code="0x45" category="fixed" width="0" label="the empty list (i.e. the list with no elements)"/>] */
TEST_FUNCTION(amqpvalue_decode_list_empty_list_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0x45 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_385: [<encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_zero_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xC0, 0x00, 0x00 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_385: [<encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_1_null_item_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xC0, 0x01, 0x01, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item1;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    item1 = amqpvalue_get_list_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(uint32_t, 1, item_count);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item1));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_385: [<encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_2_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xC0, 0x02, 0x02, 0x40, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item1;
    AMQP_VALUE item2;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 2, item_count);
    item1 = amqpvalue_get_list_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item1));
    item2 = amqpvalue_get_list_item(decoded_values[0], 1);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item2));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
    amqpvalue_destroy(item2);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_385: [<encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_255_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[3 + 255] = { 0xC0, 0xFF, 0xFF };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();
    (void)memset(&bytes[3], 0x40, 255);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 255, item_count);
    for (i = 0; i < 255; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], 0);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_385: [<encoding name="list8" code="0xc0" category="compound" width="1" label="up to 2^8 - 1 list elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_255_null_items_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[3 + 255] = { 0xC0, 0xFF, 0xFF };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();
    (void)memset(&bytes[3], 0x40, 255);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 255, item_count);
    for (i = 0; i < 255; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_zero_items_not_enough_bytes_does_not_trigger_callback_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xC0, 0x00 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_1_item_not_enough_bytes_does_not_trigger_callback_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xC0, 0x01, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xC0_255_null_items_not_enough_bytes_does_not_trigger_callback_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[3 + 254] = { 0xC0, 0xFF, 0xFF };
    umock_c_reset_all_calls();
    (void)memset(&bytes[3], 0x40, 254);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_zero_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xD0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_1_null_item_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xD0, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 1, item_count);
    item = amqpvalue_get_list_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
    amqpvalue_destroy(item);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_2_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xD0, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x40, 0x40 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 2, item_count);
    for (i = 0; i < 2; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_255_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[9 + 255] = { 0xD0, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();
    (void)memset(bytes + 9, 0x40, 255);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 255, item_count);
    for (i = 0; i < 255; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_256_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[9 + 256] = { 0xD0, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();
    (void)memset(bytes + 9, 0x40, 256);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 256, item_count);
    for (i = 0; i < 256; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_383: [1.6.22 list A sequence of polymorphic values.] */
/* Tests_SRS_AMQPVALUE_01_386: [<encoding name="list32" code="0xd0" category="compound" width="4" label="up to 2^32 - 1 list elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_256_null_items_byte_by_byte_succeeds)
{
    // arrange
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[9 + 256] = { 0xD0, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();
    (void)memset(bytes + 9, 0x40, 256);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    for (i = 0; i < sizeof(bytes); i++)
    {
        int result = amqpvalue_decode_bytes(amqpvalue_decoder, &bytes[i], 1);
        ASSERT_ARE_EQUAL(int, 0, result);
    }

    // assert
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LIST, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_list_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 256, item_count);
    for (i = 0; i < 256; i++)
    {
        AMQP_VALUE item = amqpvalue_get_list_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_zero_items_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xD0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_1_item_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xD0, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01 };
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_327: [If not enough bytes have accumulated to decode a value, the value_decoded_callback shall not be called.] */
TEST_FUNCTION(amqpvalue_decode_list_0xD0_256_null_items_not_enough_bytes_does_not_trigger_callback)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[9 + 255] = { 0xD0, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00 };
    umock_c_reset_all_calls();
    (void)memset(bytes + 9, 0x40, 255);

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_empty_array_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x01, 0x00 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_zero_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x00, 0x00 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_1_null_item_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x01, 0x01, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item1;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    item1 = amqpvalue_get_array_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(uint32_t, 1, item_count);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item1));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_2_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x01, 0x02, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item1;
    AMQP_VALUE item2;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 2, item_count);
    item1 = amqpvalue_get_array_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item1));
    item2 = amqpvalue_get_array_item(decoded_values[0], 1);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item2));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
    amqpvalue_destroy(item2);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_1_long_item_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x09, 0x01, 0x81, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
    //0xE0,0x11,0x02,0x81,0x7F,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x7F,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF
    uint32_t item_count;
    AMQP_VALUE item1;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    item1 = amqpvalue_get_array_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(uint32_t, 1, item_count);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LONG, (int)amqpvalue_get_type(item1));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_2_long_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xE0, 0x11, 0x02, 0x81, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

    uint32_t item_count;
    AMQP_VALUE item1;
    AMQP_VALUE item2;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    item1 = amqpvalue_get_array_item(decoded_values[0], 0);
    item2 = amqpvalue_get_array_item(decoded_values[0], 1);
    ASSERT_ARE_EQUAL(uint32_t, 2, item_count);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LONG, (int)amqpvalue_get_type(item1));
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_LONG, (int)amqpvalue_get_type(item2));

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
    amqpvalue_destroy(item1);
    amqpvalue_destroy(item2);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_398: [<encoding name="array8" code="0xe0" category="array" width="1" label="up to 2^8 - 1 array elements with total size less than 2^8 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xE0_255_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[4] = { 0xE0, 0x01, 0xFF, 0x40 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 255, item_count);
    for (i = 0; i < 255; i++)
    {
        AMQP_VALUE item = amqpvalue_get_array_item(decoded_values[0], 0);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_399: [<encoding name="array32" code="0xf0" category="array" width="4" label="up to 2^32 - 1 array elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xF0_zero_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 0, item_count);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_399: [<encoding name="array32" code="0xf0" category="array" width="4" label="up to 2^32 - 1 array elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xF0_1_null_item_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xF0, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x40 };
    uint32_t item_count;
    AMQP_VALUE item;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG));

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 1, item_count);
    item = amqpvalue_get_array_item(decoded_values[0], 0);
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
    amqpvalue_destroy(item);

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_399: [<encoding name="array32" code="0xf0" category="array" width="4" label="up to 2^32 - 1 array elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xF0_2_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[] = { 0xF0, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x40 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 2, item_count);
    for (i = 0; i < 2; i++)
    {
        AMQP_VALUE item = amqpvalue_get_array_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_399: [<encoding name="array32" code="0xf0" category="array" width="4" label="up to 2^32 - 1 array elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xF0_255_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[10] = { 0xF0, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0xFF, 0x40 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 255, item_count);
    for (i = 0; i < 255; i++)
    {
        AMQP_VALUE item = amqpvalue_get_array_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

/* Tests_SRS_AMQPVALUE_01_397: [1.6.24 array A sequence of values of a single type.] */
/* Tests_SRS_AMQPVALUE_01_399: [<encoding name="array32" code="0xf0" category="array" width="4" label="up to 2^32 - 1 array elements with total size less than 2^32 octets"/>] */
TEST_FUNCTION(amqpvalue_decode_array_0xF0_256_null_items_succeeds)
{
    // arrange
    int result;
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder = amqpvalue_decoder_create(value_decoded_callback, test_context);
    unsigned char bytes[10] = { 0xF0, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x01, 0x00, 0x40 };
    int i;
    uint32_t item_count;
    umock_c_reset_all_calls();

    STRICT_EXPECTED_CALL(gballoc_malloc(IGNORED_NUM_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(gballoc_free(IGNORED_PTR_ARG))
        .IgnoreAllCalls();
    STRICT_EXPECTED_CALL(value_decoded_callback(test_context, IGNORED_PTR_ARG))
        .IgnoreAllCalls();

    // act
    result = amqpvalue_decode_bytes(amqpvalue_decoder, bytes, sizeof(bytes));

    // assert
    ASSERT_ARE_EQUAL(int, 0, result);
    ASSERT_ARE_EQUAL(char_ptr, umock_c_get_expected_calls(), umock_c_get_actual_calls());
    ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_ARRAY, (int)amqpvalue_get_type(decoded_values[0]));
    (void)amqpvalue_get_array_item_count(decoded_values[0], &item_count);
    ASSERT_ARE_EQUAL(uint32_t, 256, item_count);
    for (i = 0; i < 256; i++)
    {
        AMQP_VALUE item = amqpvalue_get_array_item(decoded_values[0], i);
        ASSERT_ARE_EQUAL(int, (int)AMQP_TYPE_NULL, (int)amqpvalue_get_type(item));
        amqpvalue_destroy(item);
    }

    // cleanup
    amqpvalue_decoder_destroy(amqpvalue_decoder);
}

END_TEST_SUITE(amqpvalue_ut)

"""