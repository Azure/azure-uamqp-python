#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from libc cimport stdint


cdef extern from "azure_uamqp_c/amqpvalue_to_string.h":

    char* amqpvalue_to_string(AMQP_VALUE amqp_value)


cdef extern from "azure_uamqp_c/amqp_types.h":

    cdef enum AMQP_TYPE_TAG:
        AMQP_TYPE_NULL,
        AMQP_TYPE_BOOL,
        AMQP_TYPE_UBYTE,
        AMQP_TYPE_USHORT,
        AMQP_TYPE_UINT,
        AMQP_TYPE_ULONG,
        AMQP_TYPE_BYTE,
        AMQP_TYPE_SHORT,
        AMQP_TYPE_INT,
        AMQP_TYPE_LONG,
        AMQP_TYPE_FLOAT,
        AMQP_TYPE_DOUBLE,
        AMQP_TYPE_CHAR,
        AMQP_TYPE_TIMESTAMP,
        AMQP_TYPE_UUID,
        AMQP_TYPE_BINARY,
        AMQP_TYPE_STRING,
        AMQP_TYPE_SYMBOL,
        AMQP_TYPE_LIST,
        AMQP_TYPE_MAP,
        AMQP_TYPE_ARRAY,
        AMQP_TYPE_DESCRIBED,
        AMQP_TYPE_COMPOSITE,
        AMQP_TYPE_UNKNOWN


cdef extern from "azure_uamqp_c/amqpvalue.h":

    ctypedef struct AMQP_VALUE:
        pass

    ctypedef unsigned char uuid[16]
    ctypedef stdint.int64_t timestamp

    cdef struct amqp_binary_TAG:
        void* bytes
        stdint.uint32_t length
    
    ctypedef amqp_binary_TAG amqp_binary

    # type handling
    AMQP_VALUE amqpvalue_create_null()
    AMQP_VALUE amqpvalue_create_boolean(bint bool_value)
    int amqpvalue_get_boolean(AMQP_VALUE value, bint* bool_value)
    AMQP_VALUE amqpvalue_create_ubyte(unsigned char ubyte_value)
    int amqpvalue_get_ubyte(AMQP_VALUE value, unsigned char* ubyte_value)
    AMQP_VALUE amqpvalue_create_ushort(stdint.uint16_t ushort_value)
    int amqpvalue_get_ushort(AMQP_VALUE value, stdint.uint16_t* ushort_value)
    AMQP_VALUE amqpvalue_create_uint(stdint.uint32_t uint_value)
    int amqpvalue_get_uint(AMQP_VALUE value, stdint.uint32_t* uint_value)
    AMQP_VALUE amqpvalue_create_ulong(stdint.uint64_t ulong_value)
    int amqpvalue_get_ulong(AMQP_VALUE value, stdint.uint64_t* ulong_value)
    AMQP_VALUE amqpvalue_create_byte(char byte_value)
    int amqpvalue_get_byte(AMQP_VALUE value, char* byte_value)
    AMQP_VALUE amqpvalue_create_short(stdint.int16_t short_value)
    int amqpvalue_get_short(AMQP_VALUE value, stdint.int16_t* short_value)
    AMQP_VALUE amqpvalue_create_int(stdint.int32_t int_value)
    int amqpvalue_get_int(AMQP_VALUE value, stdint.int32_t* int_value)
    AMQP_VALUE amqpvalue_create_long(stdint.int64_t long_value)
    int amqpvalue_get_long(AMQP_VALUE value, stdint.int64_t* long_value)
    AMQP_VALUE amqpvalue_create_float(float float_value)
    int amqpvalue_get_float(AMQP_VALUE value, float* float_value)
    AMQP_VALUE amqpvalue_create_double(double double_value)
    int amqpvalue_get_double(AMQP_VALUE value, double* double_value)
    AMQP_VALUE amqpvalue_create_char(stdint.uint32_t char_value)
    int amqpvalue_get_char(AMQP_VALUE value, stdint.uint32_t* char_value)
    AMQP_VALUE amqpvalue_create_timestamp(stdint.int64_t timestamp_value)
    int amqpvalue_get_timestamp(AMQP_VALUE value, stdint.int64_t* timestamp_value)
    AMQP_VALUE amqpvalue_create_uuid(uuid uuid_value)
    int amqpvalue_get_uuid(AMQP_VALUE value, uuid* uuid_value)
    AMQP_VALUE amqpvalue_create_binary(amqp_binary binary_value)
    int amqpvalue_get_binary(AMQP_VALUE value, amqp_binary* binary_value)
    AMQP_VALUE amqpvalue_create_string(char* string_value)
    int amqpvalue_get_string(AMQP_VALUE value, char** string_value)
    AMQP_VALUE amqpvalue_create_symbol(char* symbol_value)
    int amqpvalue_get_symbol(AMQP_VALUE value, char** symbol_value)
    AMQP_VALUE amqpvalue_create_list()
    int amqpvalue_set_list_item_count(AMQP_VALUE list, stdint.uint32_t count)
    int amqpvalue_get_list_item_count(AMQP_VALUE list, stdint.uint32_t* count)
    int amqpvalue_set_list_item(AMQP_VALUE list, stdint.uint32_t index, AMQP_VALUE list_item_value)
    AMQP_VALUE amqpvalue_get_list_item(AMQP_VALUE list, size_t index)
    AMQP_VALUE amqpvalue_create_map()
    int amqpvalue_set_map_value(AMQP_VALUE map, AMQP_VALUE key, AMQP_VALUE value)
    AMQP_VALUE amqpvalue_get_map_value(AMQP_VALUE map, AMQP_VALUE key)
    int amqpvalue_get_map_pair_count(AMQP_VALUE map, stdint.uint32_t* pair_count)
    int amqpvalue_get_map_key_value_pair(AMQP_VALUE map, stdint.uint32_t index, AMQP_VALUE* key, AMQP_VALUE* value)
    int amqpvalue_get_map(AMQP_VALUE from_value, AMQP_VALUE* map)  # TODO
    AMQP_TYPE_TAG amqpvalue_get_type(AMQP_VALUE value)
    void amqpvalue_destroy(AMQP_VALUE value)
    bint amqpvalue_are_equal(AMQP_VALUE value1, AMQP_VALUE value2)
    AMQP_VALUE amqpvalue_clone(AMQP_VALUE value)

    # encoding
    ctypedef int (*AMQPVALUE_ENCODER_OUTPUT)(void *context, unsigned char* bytes, size_t length)
    int amqpvalue_encode(AMQP_VALUE value, AMQPVALUE_ENCODER_OUTPUT encoder_output, void* context)
    int amqpvalue_get_encoded_size(AMQP_VALUE value, size_t* encoded_size)

    # decoding
    ctypedef struct AMQPVALUE_DECODER_HANDLE:
        pass
    ctypedef void(*ON_VALUE_DECODED)(void* context, AMQP_VALUE decoded_value)
    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder_create(ON_VALUE_DECODED on_value_decoded, void* callback_context)
    void amqpvalue_decoder_destroy(AMQPVALUE_DECODER_HANDLE handle)
    int amqpvalue_decode_bytes(AMQPVALUE_DECODER_HANDLE handle, unsigned char* buffer, size_t size)

    # misc for now
    AMQP_VALUE amqpvalue_create_array()
    int amqpvalue_get_array_item_count(AMQP_VALUE value, stdint.uint32_t* count)
    int amqpvalue_add_array_item(AMQP_VALUE value, AMQP_VALUE array_item_value)
    AMQP_VALUE amqpvalue_get_array_item(AMQP_VALUE value, stdint.uint32_t index)
    int amqpvalue_get_array(AMQP_VALUE value, AMQP_VALUE* array_value)
    AMQP_VALUE amqpvalue_get_inplace_descriptor(AMQP_VALUE value)
    AMQP_VALUE amqpvalue_get_inplace_described_value(AMQP_VALUE value)
    AMQP_VALUE amqpvalue_create_composite(AMQP_VALUE descriptor, stdint.uint32_t list_size)
    int amqpvalue_set_composite_item(AMQP_VALUE value, stdint.uint32_t index, AMQP_VALUE item_value)
    AMQP_VALUE amqpvalue_get_composite_item(AMQP_VALUE value, size_t index)
    AMQP_VALUE amqpvalue_create_described(AMQP_VALUE descriptor, AMQP_VALUE value)
    AMQP_VALUE amqpvalue_create_composite_with_ulong_descriptor(stdint.uint64_t descriptor)
    AMQP_VALUE amqpvalue_get_list_item_in_place(AMQP_VALUE value, size_t index)
    AMQP_VALUE amqpvalue_get_composite_item_in_place(AMQP_VALUE value, size_t index)
    int amqpvalue_get_composite_item_count(AMQP_VALUE value, stdint.uint32_t* item_count)
