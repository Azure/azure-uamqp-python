// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#ifndef AMQPVALUE_H
#define AMQPVALUE_H

#include "azure_uamqp_c/amqp_types.h"

#ifdef __cplusplus
#include <cstddef>
#include <cstdint>
extern "C" {
#else
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#endif /* __cplusplus */

    typedef struct AMQP_VALUE_DATA_TAG* AMQP_VALUE;
    typedef unsigned char uuid[16];
    typedef int64_t timestamp;

    typedef struct amqp_binary_TAG
    {
        const void* bytes;
        uint32_t length;
    } amqp_binary;

    /* type handling */
    AMQP_VALUE amqpvalue_create_null(void);
    AMQP_VALUE amqpvalue_create_boolean(int bool_value);
    int amqpvalue_get_boolean(AMQP_VALUE value, int* bool_value);
    AMQP_VALUE amqpvalue_create_ubyte(unsigned char ubyte_value);
    int amqpvalue_get_ubyte(AMQP_VALUE value, unsigned char* ubyte_value);
    AMQP_VALUE amqpvalue_create_ushort(uint16_t ushort_value);
    int amqpvalue_get_ushort(AMQP_VALUE value, uint16_t* ushort_value);
    AMQP_VALUE amqpvalue_create_uint(uint32_t uint_value);
    int amqpvalue_get_uint(AMQP_VALUE value, uint32_t* uint_value);
    AMQP_VALUE amqpvalue_create_ulong(uint64_t ulong_value);
    int amqpvalue_get_ulong(AMQP_VALUE value, uint64_t* ulong_value);
    AMQP_VALUE amqpvalue_create_byte(char byte_value);
    int amqpvalue_get_byte(AMQP_VALUE value, char* byte_value);
    AMQP_VALUE amqpvalue_create_short(int16_t short_value);
    int amqpvalue_get_short(AMQP_VALUE value, int16_t* short_value);
    AMQP_VALUE amqpvalue_create_int(int32_t int_value);
    int amqpvalue_get_int(AMQP_VALUE value, int32_t* int_value);
    AMQP_VALUE amqpvalue_create_long(int64_t long_value);
    int amqpvalue_get_long(AMQP_VALUE value, int64_t* long_value);
    AMQP_VALUE amqpvalue_create_float(float float_value);
    int amqpvalue_get_float(AMQP_VALUE value, float* float_value);
    AMQP_VALUE amqpvalue_create_double(double double_value);
    int amqpvalue_get_double(AMQP_VALUE value, double* double_value);
    AMQP_VALUE amqpvalue_create_char(uint32_t char_value);
    int amqpvalue_get_char(AMQP_VALUE value, uint32_t* char_value);
    AMQP_VALUE amqpvalue_create_timestamp(int64_t timestamp_value);
    int amqpvalue_get_timestamp(AMQP_VALUE value, int64_t* timestamp_value);
    AMQP_VALUE amqpvalue_create_uuid(uuid uuid_value);
    int amqpvalue_get_uuid(AMQP_VALUE value, uuid* uuid_value);
    AMQP_VALUE amqpvalue_create_binary(amqp_binary binary_value);
    int amqpvalue_get_binary(AMQP_VALUE value, amqp_binary* binary_value);
    AMQP_VALUE amqpvalue_create_string(const char* string_value);
    int amqpvalue_get_string(AMQP_VALUE value, const char** string_value);
    AMQP_VALUE amqpvalue_create_symbol(const char* symbol_value);
    int amqpvalue_get_symbol(AMQP_VALUE value, const char** symbol_value);

    AMQP_VALUE amqpvalue_create_list(void);
    int amqpvalue_set_list_item_count(AMQP_VALUE list, uint32_t count);
    int amqpvalue_get_list_item_count(AMQP_VALUE list, uint32_t* count);
    int amqpvalue_set_list_item(AMQP_VALUE list, uint32_t index, AMQP_VALUE list_item_value);
    AMQP_VALUE amqpvalue_get_list_item(AMQP_VALUE list, size_t index);

    AMQP_VALUE amqpvalue_create_map(void);
    int amqpvalue_set_map_value(AMQP_VALUE map, AMQP_VALUE key, AMQP_VALUE value);
    AMQP_VALUE amqpvalue_get_map_value(AMQP_VALUE map, AMQP_VALUE key);
    int amqpvalue_get_map_pair_count(AMQP_VALUE map, uint32_t* pair_count);
    int amqpvalue_get_map_key_value_pair(AMQP_VALUE map, uint32_t index, AMQP_VALUE* key, AMQP_VALUE* value);
    int amqpvalue_get_map(AMQP_VALUE from_value, AMQP_VALUE* map);
    AMQP_VALUE amqpvalue_create_array(void);
    int amqpvalue_add_array_item(AMQP_VALUE value, AMQP_VALUE array_item_value);
    AMQP_VALUE amqpvalue_get_array_item(AMQP_VALUE value, uint32_t index);
    int amqpvalue_get_array_item_count(AMQP_VALUE value, uint32_t* count);
    int amqpvalue_get_array(AMQP_VALUE value, AMQP_VALUE* array_value);
    AMQP_TYPE amqpvalue_get_type(AMQP_VALUE value);

    void amqpvalue_destroy(AMQP_VALUE value);

    bool amqpvalue_are_equal(AMQP_VALUE value1, AMQP_VALUE value2);
    AMQP_VALUE amqpvalue_clone(AMQP_VALUE value);

    /* encoding */
    typedef int (*AMQPVALUE_ENCODER_OUTPUT)(void* context, const unsigned char* bytes, size_t length);

    int amqpvalue_encode(AMQP_VALUE value, AMQPVALUE_ENCODER_OUTPUT encoder_output, void* context);
    int amqpvalue_get_encoded_size(AMQP_VALUE value, size_t* encoded_size);

    /* decoding */
    typedef struct AMQPVALUE_DECODER_HANDLE_DATA_TAG* AMQPVALUE_DECODER_HANDLE;
    typedef void(*ON_VALUE_DECODED)(void* context, AMQP_VALUE decoded_value);

    AMQPVALUE_DECODER_HANDLE amqpvalue_decoder_create(ON_VALUE_DECODED on_value_decoded, void* callback_context);
    void amqpvalue_decoder_destroy(AMQPVALUE_DECODER_HANDLE handle);
    int amqpvalue_decode_bytes(AMQPVALUE_DECODER_HANDLE handle, const unsigned char* buffer, size_t size);

    /* misc for now, not spec'd */
    AMQP_VALUE amqpvalue_get_inplace_descriptor(AMQP_VALUE value);
    AMQP_VALUE amqpvalue_get_inplace_described_value(AMQP_VALUE value);

    AMQP_VALUE amqpvalue_create_composite(AMQP_VALUE descriptor, uint32_t list_size);
    int amqpvalue_set_composite_item(AMQP_VALUE value, uint32_t index, AMQP_VALUE item_value);
    AMQP_VALUE amqpvalue_get_composite_item(AMQP_VALUE value, size_t index);
    AMQP_VALUE amqpvalue_create_described(AMQP_VALUE descriptor, AMQP_VALUE value);
    AMQP_VALUE amqpvalue_create_composite_with_ulong_descriptor(uint64_t descriptor);
    AMQP_VALUE amqpvalue_get_list_item_in_place(AMQP_VALUE value, size_t index);
    AMQP_VALUE amqpvalue_get_composite_item_in_place(AMQP_VALUE value, size_t index);
    int amqpvalue_get_composite_item_count(AMQP_VALUE value, uint32_t* item_count);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* AMQPVALUE_H */
